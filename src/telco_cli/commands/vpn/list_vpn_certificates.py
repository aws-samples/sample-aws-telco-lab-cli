# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""List VPN certificates command."""

import argparse
import time
from typing import Any, Dict, List, Optional

import boto3
from rich.console import Console
from rich.table import Table

from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, console_error, get_logger

# Get logger for this module
logger = get_logger(__name__)


class ListVPNCertificatesCommand(BaseCommand):
    """List active VPN certificates."""

    def __init__(self):
        self.console = Console()

    @property
    def name(self) -> str:
        return "list-vpn-certificates"

    @property
    def description(self) -> str:
        return "List active VPN certificates"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--show-details", action="store_true", help="Show detailed certificate information"
        )
        parser.add_argument(
            "--output",
            choices=["json", "table"],
            default="table",
            help="Output format (default: table)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the list VPN certificates command."""
        try:
            console.print("📋 [bold cyan]Listing VPN certificates...[/bold cyan]")
            logger.info("Starting list VPN certificates command")

            # Step 1: Discover OpenVPN server
            console.print("\n🔍 Discovering OpenVPN server...")
            server_info = self._discover_openvpn_server()
            if not server_info:
                raise Exception("No OpenVPN server found or accessible")
            console.print(
                f"✅ Found OpenVPN server: [green]{server_info['name']} ({server_info['instance_id']})[/green]"
            )
            logger.debug(f"Server info: {server_info}")

            # Step 2: Check SSM connectivity
            console.print("\n🔌 Checking SSM connectivity...")
            if not self._check_ssm_connectivity(server_info["instance_id"]):
                raise Exception(
                    "OpenVPN server is not accessible via SSM. Please ensure SSM agent is running."
                )
            console.print("✅ SSM connectivity confirmed")

            # Step 3: Get list of issued certificates
            console.print("\n🔎 Retrieving certificate list...")
            certificates = self._get_issued_certificates(server_info["instance_id"])
            logger.debug(f"Found {len(certificates)} certificates")

            # Step 4: Get certificate details if requested
            cert_details = {}
            if args.show_details and certificates:
                console.print("\n📊 Retrieving certificate details...")
                cert_details = self._get_certificate_details(
                    server_info["instance_id"], certificates
                )
                logger.debug(f"Retrieved details for {len(cert_details)} certificates")

            # Step 5: Get CCD configurations
            ccd_configs = self._get_ccd_configurations(server_info["instance_id"])
            logger.debug(f"Found {len(ccd_configs)} CCD configurations")

            # Display results
            if args.output == "table":
                self._display_certificates_table(
                    server_info, certificates, ccd_configs, cert_details, args.show_details
                )
            else:
                self._display_certificates_json(
                    server_info, certificates, ccd_configs, cert_details, args.show_details
                )

        except Exception as e:
            console_error.print(f"❌ [red]Failed to list VPN certificates: {str(e)}[/red]")
            logger.exception("Failed to list VPN certificates")
            raise

    def _display_certificates_table(
        self,
        server_info: Dict[str, Any],
        certificates: List[str],
        ccd_configs: Dict[str, List[str]],
        cert_details: Dict[str, Dict[str, Any]],
        show_details: bool,
    ) -> None:
        """Display certificates in rich table format."""
        # Server info panel
        self.console.print("\n🎯 [bold]VPN Server Information:[/bold]")
        self.console.print(f"├── Instance ID: [cyan]{server_info['instance_id']}[/cyan]")
        self.console.print(f"├── Name: [cyan]{server_info['name']}[/cyan]")
        self.console.print(
            f"├── Endpoint: [cyan]{server_info['endpoint']}:{server_info['port']}[/cyan]"
        )
        self.console.print(f"└── Network: [cyan]{server_info['network']}[/cyan]")

        if not certificates:
            self.console.print("\n📭 [yellow]No certificates found[/yellow]")
            return

        # Certificates table
        self.console.print(f"\n📜 [bold]Active Certificates ({len(certificates)} total):[/bold]")

        table = Table(title="VPN Certificates")
        table.add_column("Certificate Name", style="yellow", no_wrap=True)
        table.add_column("Routing Status", style="blue")
        table.add_column("Allowed Subnets", style="green")

        if show_details:
            table.add_column("Valid From", style="cyan")
            table.add_column("Valid Until", style="cyan")
            table.add_column("Serial Number", style="dim")

        for cert in certificates:
            # Routing status and subnets
            if cert in ccd_configs:
                routing_status = "[green]✅ Configured[/green]"
                subnets = ", ".join(ccd_configs[cert])
            else:
                routing_status = "[dim]❌ Not configured[/dim]"
                subnets = "[dim]None[/dim]"

            row_data = [cert, routing_status, subnets]

            # Add details if requested
            if show_details:
                if cert in cert_details:
                    details = cert_details[cert]
                    row_data.extend(
                        [
                            details.get("ValidFrom", "Unknown"),
                            details.get("ValidUntil", "Unknown"),
                            details.get("SerialNumber", "Unknown"),
                        ]
                    )
                else:
                    row_data.extend(["Unknown", "Unknown", "Unknown"])

            table.add_row(*row_data)

        self.console.print(table)
        self.console.print(
            f"\n📊 [bold green]Summary:[/bold green] {len(certificates)} active certificate(s)"
        )

    def _display_certificates_json(
        self,
        server_info: Dict[str, Any],
        certificates: List[str],
        ccd_configs: Dict[str, List[str]],
        cert_details: Dict[str, Dict[str, Any]],
        show_details: bool,
    ) -> None:
        """Display certificates in JSON format (legacy)."""
        console.print("\n🎯 [bold]VPN Server Information:[/bold]")
        console.print(f"├── Instance ID: [cyan]{server_info['instance_id']}[/cyan]")
        console.print(f"├── Name: [cyan]{server_info['name']}[/cyan]")
        console.print(f"├── Endpoint: [cyan]{server_info['endpoint']}:{server_info['port']}[/cyan]")
        console.print(f"└── Network: [cyan]{server_info['network']}[/cyan]")

        console.print("\n📜 [bold]Active Certificates:[/bold]")
        if not certificates:
            console.print("└── [dim]No certificates found[/dim]")
        else:
            for index, cert in enumerate(certificates):
                is_last = index == len(certificates) - 1
                prefix = "└──" if is_last else "├──"
                child_prefix = "    " if is_last else "│   "

                console.print(f"{prefix} [yellow]{cert}[/yellow]")

                if cert in ccd_configs:
                    console.print(f"{child_prefix}├── Routing: [green]Configured[/green]")
                    console.print(f"{child_prefix}└── Allowed Subnets:")
                    routes = ccd_configs[cert]
                    for route_index, route in enumerate(routes):
                        route_prefix = "└──" if route_index == len(routes) - 1 else "├──"
                        console.print(f"{child_prefix}    {route_prefix} [blue]{route}[/blue]")
                else:
                    console.print(f"{child_prefix}└── Routing: [dim]Not configured[/dim]")

                if show_details and cert in cert_details:
                    details = cert_details[cert]
                    if details.get("ValidFrom"):
                        console.print(
                            f"{child_prefix}    ├── Valid From: [green]{details['ValidFrom']}[/green]"
                        )
                    if details.get("ValidUntil"):
                        console.print(
                            f"{child_prefix}    ├── Valid Until: [green]{details['ValidUntil']}[/green]"
                        )
                    if details.get("SerialNumber"):
                        console.print(
                            f"{child_prefix}    └── Serial: [dim]{details['SerialNumber']}[/dim]"
                        )

        console.print(
            f"\n📊 [bold green]Summary:[/bold green] {len(certificates)} active certificate(s)"
        )

    def _discover_openvpn_server(self) -> Optional[Dict[str, Any]]:
        """Discover OpenVPN server instance."""
        ec2 = boto3.client("ec2")
        logger.debug("Starting OpenVPN server discovery")

        # Try different filter combinations
        filter_sets = [
            # Specific known OpenVPN server names
            [
                {"Name": "tag:Name", "Values": ["lab-ovpn-server", "ovpn-server"]},
                {"Name": "instance-state-name", "Values": ["running"]},
            ],
            # Generic OpenVPN names
            [
                {"Name": "tag:Name", "Values": ["*OpenVPN*", "*openvpn*", "*VPN*", "*vpn*"]},
                {"Name": "instance-state-name", "Values": ["running"]},
            ],
            # By security group names
            [
                {"Name": "instance-state-name", "Values": ["running"]},
                {"Name": "group-name", "Values": ["*vpn*", "*openvpn*"]},
            ],
        ]

        for filters in filter_sets:
            try:
                logger.debug(f"Trying filters: {filters}")
                response = ec2.describe_instances(Filters=filters)

                for reservation in response.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        if instance.get("InstanceId") and instance.get("PublicIpAddress"):
                            # Get instance name from tags
                            name = "Unknown"
                            for tag in instance.get("Tags", []):
                                if tag["Key"] == "Name":
                                    name = tag["Value"]
                                    break

                            # Prefer DNS name over IP
                            endpoint = instance.get("PublicDnsName", "").strip()
                            if not endpoint:
                                endpoint = instance["PublicIpAddress"]

                            logger.info(f"Found OpenVPN server: {name} ({instance['InstanceId']})")
                            return {
                                "instance_id": instance["InstanceId"],
                                "name": name,
                                "endpoint": endpoint,
                                "public_ip": instance["PublicIpAddress"],
                                "public_dns": instance.get("PublicDnsName", ""),
                                "private_ip": instance.get("PrivateIpAddress", ""),
                                "private_dns": instance.get("PrivateDnsName", ""),
                                "port": 1194,  # Default OpenVPN port
                                "protocol": "udp",
                                "cipher": "AES-256-CBC",
                                "auth": "SHA256",
                                "network": "10.10.10.0/24",
                            }
            except Exception as e:
                if "InvalidClientTokenId" in str(e) or "UnauthorizedException" in str(e):
                    raise Exception(
                        'AWS credentials are invalid or not configured. Please run "aws configure" to set up your credentials.'
                    )
                logger.debug(f"Filter set failed: {e}")
                continue

        logger.warning("No OpenVPN server found")
        return None

    def _check_ssm_connectivity(self, instance_id: str) -> bool:
        """Check if instance is accessible via SSM."""
        ssm = boto3.client("ssm")

        logger.debug(f"Checking SSM connectivity for instance {instance_id}")
        try:
            response = ssm.describe_instance_information(
                Filters=[{"Key": "InstanceIds", "Values": [instance_id]}]
            )

            if response.get("InstanceInformationList"):
                instance_info = response["InstanceInformationList"][0]
                ping_status = instance_info.get("PingStatus")
                logger.debug(f"Instance SSM ping status: {ping_status}")
                return ping_status == "Online"

            logger.debug("No instance information found in SSM")
            return False
        except Exception as e:
            logger.debug(f"SSM connectivity check failed: {e}")
            return False

    def _get_issued_certificates(self, instance_id: str) -> List[str]:
        """Get list of issued certificates."""
        commands = [
            "cd /etc/openvpn/easy-rsa",
            'ls pki/issued/*.crt 2>/dev/null | grep -v "ca.crt" | sed "s|pki/issued/||g" | sed "s|.crt||g" || echo "NO_CERTIFICATES"',
        ]

        logger.debug(f"Getting issued certificates from {instance_id}")
        result = self._run_ssm_command(instance_id, " && ".join(commands))
        stdout = result.get("StandardOutputContent", "")

        if stdout.strip() == "NO_CERTIFICATES" or not stdout.strip():
            logger.debug("No certificates found")
            return []

        certificates = [cert.strip() for cert in stdout.strip().split("\n") if cert.strip()]
        logger.debug(f"Found certificates: {certificates}")
        return certificates

    def _get_certificate_details(
        self, instance_id: str, cert_names: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """Get certificate details for each certificate."""
        details = {}

        for cert_name in cert_names:
            # Use a single command string to avoid issues with && joining
            command = f"""cd /etc/openvpn/easy-rsa && \
if [ -f pki/issued/{cert_name}.crt ]; then \
  openssl x509 -in pki/issued/{cert_name}.crt -noout -subject -dates -serial; \
else \
  echo "Certificate not found"; \
fi"""

            try:
                result = self._run_ssm_command(instance_id, command)
                stdout = result.get("StandardOutputContent", "")
                details[cert_name] = self._parse_certificate_details(stdout)
            except Exception:
                details[cert_name] = {"Error": "Could not retrieve certificate details"}

        return details

    def _parse_certificate_details(self, output: str) -> Dict[str, str]:
        """Parse certificate details from openssl output."""
        details = {}

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("subject="):
                details["Subject"] = line.replace("subject=", "")
            elif line.startswith("notBefore="):
                details["ValidFrom"] = line.replace("notBefore=", "")
            elif line.startswith("notAfter="):
                details["ValidUntil"] = line.replace("notAfter=", "")
            elif line.startswith("serial="):
                details["SerialNumber"] = line.replace("serial=", "")

        return details

    def _get_ccd_configurations(self, instance_id: str) -> Dict[str, List[str]]:
        """Get client configuration directory configurations."""
        # Use a single command string to avoid issues with && joining
        command = """cd /etc/openvpn && \
if [ -d ccd ]; then \
  for file in ccd/*; do \
    if [ -f "$file" ]; then \
      echo "=== $(basename $file) ==="; \
      grep "push.*route" "$file" 2>/dev/null || echo "No routes configured"; \
    fi; \
  done; \
else \
  echo "No CCD directory found"; \
fi"""

        try:
            result = self._run_ssm_command(instance_id, command)
            stdout = result.get("StandardOutputContent", "")
            return self._parse_ccd_configurations(stdout)
        except Exception:
            return {}

    def _parse_ccd_configurations(self, output: str) -> Dict[str, List[str]]:
        """Parse CCD configuration output."""
        configs: Dict[str, List[str]] = {}
        current_client = None

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("=== ") and line.endswith(" ==="):
                current_client = line.replace("=== ", "").replace(" ===", "")
                configs[current_client] = []
            elif current_client and line.startswith('push "route'):
                # Extract route from: push "route 192.168.1.0 255.255.255.0"
                route = line.replace('push "route ', "").replace('"', "")
                configs[current_client].append(route)

        return configs

    def _run_ssm_command(self, instance_id: str, command: str) -> Dict[str, Any]:
        """Run command on instance via SSM."""
        ssm = boto3.client("ssm")

        logger.debug(f"Running SSM command on {instance_id}: {command[:100]}...")

        # Send command
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]},
        )

        command_id = response["Command"]["CommandId"]
        logger.debug(f"SSM command ID: {command_id}")

        # Wait for command completion
        max_attempts = 30
        for i in range(max_attempts):
            time.sleep(2)

            try:
                result = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)

                if result["Status"] in ["Success", "Failed", "Cancelled", "TimedOut"]:
                    if result["Status"] != "Success":
                        error_msg = result.get("StandardErrorContent", "Unknown error")
                        logger.error(f"SSM command failed: {error_msg}")
                        raise Exception(f"Command failed: {error_msg}")

                    logger.debug("SSM command completed successfully")
                    return result
            except Exception as e:
                if "InvocationDoesNotExist" not in str(e):
                    logger.error(f"Error checking command status: {e}")
                    raise

        raise Exception(f"Command {command_id} timed out after 60 seconds")
