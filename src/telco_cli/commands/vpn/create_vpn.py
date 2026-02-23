# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Create VPN command implementation."""

import argparse
import re
import shlex
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, console_error, get_logger

logger = get_logger(__name__)

# SSM command execution constants
SSM_COMMAND_WAIT_SECONDS = 5  # Wait time for SSM command to complete before checking status
OPENVPN_RESTART_WAIT_SECONDS = 3  # Wait time after OpenVPN restart before status check

# File permission constants
OVPN_FILE_PERMISSIONS = 0o600  # Read/write for owner only
CCD_FILE_PERMISSIONS = 0o644  # Read/write for owner, read for group/others


class CreateVPNCommand(BaseCommand):
    """Generate VPN certificates for partner access."""

    def __init__(self):
        self.ec2_client: Any = None
        self.ssm_client: Any = None

    @property
    def name(self) -> str:
        return "create-vpn"

    @property
    def description(self) -> str:
        return "Generate VPN certificates for partner access"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("partner_name", help="Name of the partner to generate certificate for")
        parser.add_argument(
            "--allowed-subnets",
            required=True,
            help='Comma-separated list of allowed subnets (e.g., "192.168.100.0/24,10.0.0.0/16")',
        )
        parser.add_argument(
            "--certificate-duration", default="30d", help="Certificate duration (e.g., '30d')"
        )
        parser.add_argument("--output-dir", default=".", help="Directory to save the .ovpn file")

    def run(self, args: argparse.Namespace) -> None:
        """Execute the create-vpn command."""
        try:
            self._initialize_aws_clients()
            self._validate_inputs(
                args.partner_name, args.allowed_subnets, args.certificate_duration
            )

            console.print(
                f"🔐 [bold cyan]Generating VPN certificate for partner:[/bold cyan] {args.partner_name}"
            )
            console.print(f"📅 Duration: {args.certificate_duration}")
            console.print(f"🌐 Allowed subnets: {args.allowed_subnets}")

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
                    "OpenVPN server is not accessible via SSM. Ensure SSM agent is running."
                )
            console.print("✅ SSM connectivity confirmed")

            # Step 3: Generate certificate
            console.print("\n📄 Generating certificate...")
            self._generate_certificate(server_info["instance_id"], args.partner_name)
            console.print("✅ Certificate generated successfully")

            # Step 4: Create routing configuration
            console.print("\n🛤️ Creating routing configuration...")
            self._create_routing_config(
                server_info["instance_id"], args.partner_name, args.allowed_subnets
            )
            console.print("✅ Routing configuration created")

            # Step 5: Generate .ovpn file
            console.print("\n📝 Generating .ovpn configuration file...")
            self._generate_ovpn_file(server_info, args.partner_name)
            console.print("✅ .ovpn file generated")

            # Step 6: Download .ovpn file
            console.print("\n⬇️ Downloading configuration file...")
            ovpn_content = self._download_ovpn_file(server_info["instance_id"], args.partner_name)
            local_file_path = self._save_ovpn_file(args.partner_name, ovpn_content, args.output_dir)
            console.print(f"✅ Configuration file saved to: [bold]{local_file_path}[/bold]")

            # Step 7: Restart OpenVPN server
            console.print("\n🔄 Restarting OpenVPN server...")
            self._restart_openvpn_server(server_info["instance_id"])
            console.print("✅ OpenVPN server restarted")

            # Final instructions
            console.print("\n🎉 [bold green]VPN certificate generated successfully![/bold green]")
            console.print("\n📋 Instructions:")
            console.print(f"1. Configuration file saved to: {local_file_path}")
            console.print(f"2. Import '{Path(local_file_path).name}' into your OpenVPN client")
            console.print("3. Connect using the imported configuration")
            console.print(f"4. You will have access to subnets: {args.allowed_subnets}")
            console.print(f"5. Server endpoint: {server_info['endpoint']}:{server_info['port']}")

        except NoCredentialsError:
            console_error.print(
                "❌ [red]AWS credentials not found. Please configure your AWS credentials.[/red]"
            )
            logger.exception("AWS credentials missing")
            sys.exit(1)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ["InvalidClientTokenId", "UnauthorizedException"]:
                console_error.print("❌ [red]AWS credentials invalid. Run 'aws configure'.[/red]")
            else:
                console_error.print(f"❌ [red]AWS error: {e.response['Error']['Message']}[/red]")
            logger.exception("AWS ClientError")
            sys.exit(1)

        except Exception as error:
            console_error.print(f"❌ [red]Failed to generate VPN certificate: {error}[/red]")
            logger.exception("Unhandled error during VPN generation")
            sys.exit(1)

    def _initialize_aws_clients(self) -> None:
        """Initialize AWS clients."""
        try:
            logger.debug("Initializing AWS clients")
            self.ec2_client = boto3.client("ec2")
            self.ssm_client = boto3.client("ssm")
            logger.debug("AWS clients initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise Exception(f"Failed to initialize AWS clients: {e}")

    def _validate_inputs(
        self, partner_name: str, allowed_subnets: str, certificate_duration: str
    ) -> None:
        """Validate command inputs."""
        logger.debug(
            f"Validating inputs - partner: {partner_name}, subnets: {allowed_subnets}, duration: {certificate_duration}"
        )

        # Validate partner name format
        if not re.match(r"^[a-zA-Z0-9_-]+$", partner_name):
            raise ValueError(
                "Partner name must contain only alphanumeric characters, hyphens, and underscores"
            )

        # Validate allowed subnets
        if not allowed_subnets:
            raise ValueError("Allowed subnets are required (use --allowed-subnets)")

        # Validate each subnet format
        subnets = [s.strip() for s in allowed_subnets.split(",")]
        for subnet in subnets:
            if "/" in subnet:
                network, cidr = subnet.split("/")
                try:
                    cidr_num = int(cidr)
                    if cidr_num < 0 or cidr_num > 32:
                        raise ValueError(f"Invalid CIDR notation in subnet: {subnet}")
                except ValueError:
                    raise ValueError(f"Invalid CIDR notation in subnet: {subnet}")

                if not self._is_valid_ip_address(network):
                    raise ValueError(f"Invalid IP address in subnet: {subnet}")
            else:
                if not self._is_valid_ip_address(subnet):
                    raise ValueError(f"Invalid IP address: {subnet}")

        # Validate certificate duration
        if not re.match(r"^\d+d$", certificate_duration):
            raise ValueError("Certificate duration must be in format: 30d (days)")

        logger.debug("Input validation successful")

    def _is_valid_ip_address(self, ip: str) -> bool:
        """Validate IP address format."""
        octets = ip.split(".")
        if len(octets) != 4:
            return False

        try:
            return all(0 <= int(octet) <= 255 for octet in octets)
        except ValueError:
            return False

    def _discover_openvpn_server(self) -> Optional[Dict[str, Any]]:
        """Discover OpenVPN server instances using boto3."""
        logger.debug("Starting OpenVPN server discovery")
        try:
            # Try specific known OpenVPN server names
            logger.debug("Searching for specific OpenVPN server names")
            response = self.ec2_client.describe_instances(
                Filters=[
                    {"Name": "tag:Name", "Values": ["lab-ovpn-server", "ovpn-server"]},
                    {"Name": "instance-state-name", "Values": ["running"]},
                ]
            )

            # If no specific servers found, try generic OpenVPN names
            if not response["Reservations"]:
                logger.debug("No specific servers found, trying generic OpenVPN names")
                response = self.ec2_client.describe_instances(
                    Filters=[
                        {
                            "Name": "tag:Name",
                            "Values": ["*OpenVPN*", "*openvpn*", "*VPN*", "*vpn*"],
                        },
                        {"Name": "instance-state-name", "Values": ["running"]},
                    ]
                )

            # try by security group names
            if not response["Reservations"]:
                logger.debug("No tagged servers found, trying by security group names")
                response = self.ec2_client.describe_instances(
                    Filters=[
                        {"Name": "instance-state-name", "Values": ["running"]},
                        {"Name": "group-name", "Values": ["*vpn*", "*openvpn*"]},
                    ]
                )

            if not response["Reservations"]:
                logger.warning("No OpenVPN servers found")
                return None

            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    if instance.get("InstanceId") and instance.get("PublicIpAddress"):
                        # Prefer DNS name over IP for better resilience
                        endpoint = instance.get("PublicDnsName", "").strip()
                        if not endpoint:
                            endpoint = instance["PublicIpAddress"]

                        name = "Unknown"
                        for tag in instance.get("Tags", []):
                            if tag["Key"] == "Name":
                                name = tag["Value"]
                                break

                        server_info = {
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
                        logger.info(f"Found OpenVPN server: {name} ({instance['InstanceId']})")
                        return server_info

        except ClientError as e:
            logger.error(f"Failed to discover OpenVPN servers: {e.response['Error']['Message']}")
            raise Exception(f"Failed to discover OpenVPN servers: {e.response['Error']['Message']}")

        return None

    def _check_ssm_connectivity(self, instance_id: str) -> bool:
        """Check if instance is accessible via SSM using boto3."""
        logger.debug(f"Checking SSM connectivity for instance {instance_id}")
        try:
            response = self.ssm_client.describe_instance_information(
                Filters=[{"Key": "InstanceIds", "Values": [instance_id]}]
            )

            if response["InstanceInformationList"]:
                instance_info = response["InstanceInformationList"][0]
                is_online = instance_info.get("PingStatus") == "Online"
                logger.debug(f"SSM status for {instance_id}: {instance_info.get('PingStatus')}")
                return is_online

            logger.warning(f"No SSM information found for instance {instance_id}")
            return False
        except ClientError as e:
            logger.error(f"Failed to check SSM connectivity: {e}")
            return False

    def _run_ssm_command(self, instance_id: str, command: str) -> Dict[str, Any]:
        """Execute command on instance via SSM using boto3."""
        logger.debug(f"Executing SSM command on {instance_id}: {command[:100]}...")
        try:
            response = self.ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [command]},
            )

            command_id = response["Command"]["CommandId"]
            logger.debug(f"SSM command sent with ID: {command_id}")

            time.sleep(SSM_COMMAND_WAIT_SECONDS)

            result = self.ssm_client.get_command_invocation(
                CommandId=command_id, InstanceId=instance_id
            )

            logger.debug(f"SSM command status: {result['Status']}")

            if result["Status"] != "Success":
                error_details = self._format_ssm_error(result)
                logger.error(f"SSM command failed: {error_details}")
                raise Exception(
                    f"SSM command failed with status {result['Status']}: {error_details}"
                )

            return result

        except ClientError as e:
            logger.error(f"Failed to execute SSM command: {e}")
            raise Exception(
                f"Failed to execute SSM command on instance {instance_id}: {e.response['Error']['Message']}"
            )

    def _format_ssm_error(self, result: Dict[str, Any]) -> str:
        """Format SSM error details."""
        parts = []

        if result.get("StandardErrorContent"):
            parts.append(f"Error: {result['StandardErrorContent']}")

        if result.get("StandardOutputContent"):
            parts.append(f"Output: {result['StandardOutputContent']}")

        if result.get("StatusDetails"):
            parts.append(f"Details: {result['StatusDetails']}")

        return " | ".join(parts) if parts else "Unknown error"

    def _generate_certificate(self, instance_id: str, partner_name: str) -> None:
        """Generate VPN certificate for partner."""
        logger.info(f"Generating certificate for partner: {partner_name}")

        commands = [
            "cd /etc/openvpn/easy-rsa",
            f"rm -f pki/issued/{shlex.quote(partner_name)}.crt",
            f"rm -f pki/private/{shlex.quote(partner_name)}.key",
            f"rm -f pki/reqs/{shlex.quote(partner_name)}.req",
            f"EASYRSA_BATCH=1 ./easyrsa gen-req {shlex.quote(partner_name)} nopass",
            f"EASYRSA_BATCH=1 ./easyrsa sign-req client {shlex.quote(partner_name)}",
        ]

        command = " && ".join(commands)
        self._run_ssm_command(instance_id, command)
        logger.info(f"Certificate generated successfully for {partner_name}")

    def _create_routing_config(
        self, instance_id: str, partner_name: str, allowed_subnets: str
    ) -> None:
        """Create routing configuration for partner."""
        logger.info(f"Creating routing configuration for {partner_name}")

        subnets = [s.strip() for s in allowed_subnets.split(",")]
        route_commands = []

        # Generate push route commands for client configuration directory (CCD)
        for subnet in subnets:
            if "/" in subnet:
                network, bits = subnet.split("/")
                netmask = self._cidr_to_netmask(int(bits))
                # Push route to client for proper CCD routing
                route_commands.append(f'push "route {network} {netmask}"')
            else:
                # Push route for single IP addresses
                route_commands.append(f'push "route {subnet} 255.255.255.255"')

        ccd_content = [
            f"# Client Configuration for {partner_name}",
            "# Generated by telcocli",
            f"# Created: {datetime.now().isoformat()}",
            f"# Allowed subnets: {allowed_subnets}",
            "",
            *route_commands,
        ]

        ccd_content_str = "\\n".join(ccd_content)

        commands = [
            "mkdir -p /etc/openvpn/ccd",
            f"rm -f /etc/openvpn/ccd/{shlex.quote(partner_name)}",
            f'echo -e "{ccd_content_str}" > /etc/openvpn/ccd/{shlex.quote(partner_name)}',
            f"chmod {oct(CCD_FILE_PERMISSIONS)[2:]} /etc/openvpn/ccd/{shlex.quote(partner_name)}",
        ]

        command = " && ".join(commands)
        self._run_ssm_command(instance_id, command)
        logger.info(f"Routing configuration created for {partner_name}")

    def _generate_ovpn_file(self, server_info: Dict[str, Any], partner_name: str) -> None:
        """Generate .ovpn configuration file."""
        logger.info(f"Generating .ovpn file for {partner_name}")

        commands = [
            "cd /etc/openvpn",
            f"rm -f {shlex.quote(partner_name)}.ovpn",
            f'echo "client" > {shlex.quote(partner_name)}.ovpn',
            f'echo "dev tun" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "proto {server_info["protocol"]}" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "remote {server_info["endpoint"]} {server_info["port"]}" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "resolv-retry infinite" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "nobind" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "persist-key" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "persist-tun" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "remote-cert-tls server" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "cipher {server_info["cipher"]}" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "auth {server_info["auth"]}" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "verb 3" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "comp-lzo adaptive" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "allow-compression yes" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "<ca>" >> {shlex.quote(partner_name)}.ovpn',
            f"cat ca.crt >> {shlex.quote(partner_name)}.ovpn",
            f'echo "</ca>" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "<cert>" >> {shlex.quote(partner_name)}.ovpn',
            f"cat easy-rsa/pki/issued/{shlex.quote(partner_name)}.crt >> {shlex.quote(partner_name)}.ovpn",
            f'echo "</cert>" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "<key>" >> {shlex.quote(partner_name)}.ovpn',
            f"cat easy-rsa/pki/private/{shlex.quote(partner_name)}.key >> {shlex.quote(partner_name)}.ovpn",
            f'echo "</key>" >> {shlex.quote(partner_name)}.ovpn',
            f'echo "<tls-crypt>" >> {shlex.quote(partner_name)}.ovpn',
            f"cat ta.key >> {shlex.quote(partner_name)}.ovpn 2>/dev/null || true",
            f'echo "</tls-crypt>" >> {shlex.quote(partner_name)}.ovpn',
            f"chmod {oct(OVPN_FILE_PERMISSIONS)[2:]} {shlex.quote(partner_name)}.ovpn",
        ]

        command = " && ".join(commands)
        self._run_ssm_command(server_info["instance_id"], command)
        logger.info(f".ovpn file generated for {partner_name}")

    def _download_ovpn_file(self, instance_id: str, partner_name: str) -> str:
        """Download .ovpn file content from server."""
        logger.info(f"Downloading .ovpn file for {partner_name}")
        result = self._run_ssm_command(
            instance_id, f"cat /etc/openvpn/{shlex.quote(partner_name)}.ovpn"
        )
        content = result.get("StandardOutputContent", "")
        logger.debug(f"Downloaded .ovpn file, size: {len(content)} bytes")
        return content

    def _save_ovpn_file(self, partner_name: str, content: str, output_dir: str) -> str:
        """Save .ovpn file locally."""
        logger.info(f"Saving .ovpn file for {partner_name}")
        try:
            # Validate path traversal protection
            if ".." in output_dir:
                raise ValueError(f"Invalid output directory: {output_dir}")

            # Validate and ensure output directory exists
            output_path = Path(output_dir).resolve()
            if not str(output_path).startswith(str(Path.cwd().resolve())):
                if not str(output_path).startswith(str(Path.home().resolve())):
                    raise ValueError(f"Invalid output directory: {output_dir}")
            output_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")[:19]
            filename = f"{partner_name}_{timestamp}.ovpn"
            file_path = output_path / filename

            if not content or not content.strip():
                raise Exception("VPN configuration content is empty")

            # Write file with restricted permissions
            file_path.write_text(content)
            file_path.chmod(OVPN_FILE_PERMISSIONS)

            # File verification removed - write_text() will raise exception on failure

            logger.info(f"Saved .ovpn file to {file_path.resolve()}")
            return str(file_path.resolve())
        except Exception as error:
            logger.error(f"Failed to save VPN configuration file: {error}")
            raise Exception(f"Failed to save VPN configuration file: {error}")

    def _restart_openvpn_server(self, instance_id: str) -> None:
        """Restart OpenVPN server."""
        logger.info("Restarting OpenVPN server")

        commands = [
            "sudo systemctl restart openvpn-server@server || sudo systemctl restart openvpn@server",
            f"sleep {OPENVPN_RESTART_WAIT_SECONDS}",
            "sudo systemctl status openvpn-server@server --no-pager || sudo systemctl status openvpn@server --no-pager",
        ]

        command = " && ".join(commands)
        try:
            result = self._run_ssm_command(instance_id, command)
            logger.debug(f"OpenVPN restart output: {result.get('StandardOutputContent', '')[:200]}")
            logger.info("OpenVPN server restarted successfully")
        except Exception as e:
            logger.warning(f"OpenVPN server restart may have failed: {e}")
            console.print("[yellow]Warning: OpenVPN server restart may have failed[/yellow]")

    def _cidr_to_netmask(self, bits: int) -> str:
        """Convert CIDR bits to netmask."""
        mask = (0xFFFFFFFF << (32 - bits)) & 0xFFFFFFFF
        return ".".join(
            [
                str((mask >> 24) & 0xFF),
                str((mask >> 16) & 0xFF),
                str((mask >> 8) & 0xFF),
                str(mask & 0xFF),
            ]
        )
