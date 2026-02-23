# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Revoke VPN certificate command."""

import argparse
import shlex
import time
from typing import Any, Dict, Optional

import boto3

from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, console_error, get_logger
from telco_cli.utils.prompts import confirm_destructive_operation

# Get logger for this module
logger = get_logger(__name__)

# SSM command execution constants
SSM_COMMAND_MAX_ATTEMPTS = 30  # Maximum polling attempts for SSM command completion
SSM_COMMAND_POLL_INTERVAL = 2  # Seconds between polling attempts
SSM_COMMAND_TIMEOUT_SECONDS = SSM_COMMAND_MAX_ATTEMPTS * SSM_COMMAND_POLL_INTERVAL  # 60 seconds


class RevokeVPNCertificateCommand(BaseCommand):
    """Revoke VPN certificates for a partner."""

    @property
    def name(self) -> str:
        return "revoke-vpn-certificate"

    @property
    def description(self) -> str:
        return "Revoke VPN certificates for a partner"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("partner_name", help="Name of the partner to revoke certificate for")
        parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    def run(self, args: argparse.Namespace) -> None:
        """Execute the revoke VPN certificate command."""
        try:
            partner_name = args.partner_name

            # Validate partner name format
            if not partner_name.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    "Partner name must contain only alphanumeric characters, hyphens, and underscores"
                )

            console.print(
                f"[bold cyan]Revoking VPN certificate for partner:[/bold cyan] {partner_name}"
            )
            logger.info(f"Starting revoke VPN certificate for partner: {partner_name}")

            # Step 1: Discover OpenVPN server
            console.print("\nDiscovering OpenVPN server...")
            server_info = self._discover_openvpn_server()
            if not server_info:
                raise Exception("No OpenVPN server found or accessible")
            console.print(
                f"Found OpenVPN server: [green]{server_info['name']} ({server_info['instance_id']})[/green]"
            )
            logger.debug(f"Server info: {server_info}")

            # Step 2: Check SSM connectivity
            console.print("\n🔌 Checking SSM connectivity...")
            if not self._check_ssm_connectivity(server_info["instance_id"]):
                raise Exception(
                    "OpenVPN server is not accessible via SSM. Please ensure SSM agent is running."
                )
            console.print("✅ SSM connectivity confirmed")

            # Step 3: Check if certificate exists
            console.print("\n🔎 Checking certificate status...")
            if not self._check_certificate_exists(server_info["instance_id"], partner_name):
                console_error.print(
                    f"❌ [red]Certificate for partner '{partner_name}' not found[/red]"
                )
                logger.warning(f"Certificate for partner '{partner_name}' not found")
                return
            console.print("✅ Certificate found")

            # Confirmation prompt for destructive operation
            if not args.yes:
                details = [
                    "This action will:",
                    "• Revoke the certificate in Easy-RSA PKI",
                    "• Update the Certificate Revocation List",
                    "• Remove client configuration files",
                    "• Terminate existing VPN connections",
                ]

                if not confirm_destructive_operation(
                    operation_name="revoke VPN certificate for",
                    resource_name=f"'{partner_name}'",
                    details=details,
                    skip_confirmation=False,
                    raise_on_cancel=False,
                ):
                    return

            console.print("\nVerifying certificate still exists...")
            if not self._check_certificate_exists(server_info["instance_id"], partner_name):
                console_error.print(f"\nCertificate for partner '{partner_name}' no longer exists")
                logger.warning(f"Certificate for partner '{partner_name}' was already revoked")
                return

            # Step 4: Revoke certificate
            console.print("\n🚫 Revoking certificate...")
            self._revoke_certificate(server_info["instance_id"], partner_name)
            console.print("✅ Certificate revoked successfully")

            # Step 5: Update CRL
            console.print("\n📝 Updating Certificate Revocation List...")
            self._update_crl(server_info["instance_id"])
            console.print("✅ CRL updated successfully")

            # Step 6: Remove CCD configuration
            console.print("\n🗑️ Removing client configuration...")
            self._remove_ccd_config(server_info["instance_id"], partner_name)
            console.print("✅ Client configuration removed")

            # Step 7: Clean up certificate files
            console.print("\n🧹 Cleaning up certificate files...")
            self._cleanup_certificate_files(server_info["instance_id"], partner_name)
            console.print("✅ Certificate files cleaned up")

            # Display success message
            console.print("\n🎉 [bold green]VPN certificate revoked successfully![/bold green]")
            console.print("\n📋 [bold]Summary:[/bold]")
            console.print(f"├── Partner: [yellow]{partner_name}[/yellow]")
            console.print(f"├── Server: [cyan]{server_info['name']}[/cyan]")
            console.print("├── Status: [red]Revoked[/red]")
            console.print("└── Actions completed:")
            console.print("    ├── Certificate revoked in Easy-RSA PKI")
            console.print("    ├── Certificate Revocation List updated")
            console.print("    ├── Client configuration removed")
            console.print("    └── Certificate files cleaned up")
            console.print(
                "\n⚠️ [dim]Note: Existing VPN connections will be terminated on next CRL check[/dim]"
            )

            logger.info(f"Successfully revoked VPN certificate for partner: {partner_name}")

        except Exception as e:
            console_error.print(f"❌ [red]Failed to revoke VPN certificate: {str(e)}[/red]")
            logger.exception("Failed to revoke VPN certificate")
            raise

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

    def _check_certificate_exists(self, instance_id: str, partner_name: str) -> bool:
        """Check if certificate exists for the partner."""
        commands = [
            "cd /etc/openvpn/easy-rsa",
            f'ls pki/issued/{shlex.quote(partner_name)}.crt 2>/dev/null && echo "EXISTS" || echo "NOT_FOUND"',
        ]

        logger.debug(f"Checking if certificate exists for partner: {partner_name}")
        try:
            result = self._run_ssm_command(instance_id, " && ".join(commands))
            stdout = result.get("StandardOutputContent", "")
            exists = "EXISTS" in stdout
            logger.debug(f"Certificate exists: {exists}")
            return exists
        except Exception as e:
            logger.debug(f"Error checking certificate existence: {e}")
            return False

    def _revoke_certificate(self, instance_id: str, partner_name: str) -> None:
        """Revoke certificate using Easy-RSA."""
        commands = [
            "cd /etc/openvpn/easy-rsa",
            f"EASYRSA_BATCH=1 ./easyrsa revoke {shlex.quote(partner_name)}",
            'echo "Certificate revoked successfully"',
        ]

        logger.info(f"Revoking certificate for partner: {partner_name}")
        self._run_ssm_command(instance_id, " && ".join(commands))

    def _update_crl(self, instance_id: str) -> None:
        """Update Certificate Revocation List."""
        commands = [
            "cd /etc/openvpn/easy-rsa",
            "EASYRSA_BATCH=1 ./easyrsa gen-crl",
            "cp pki/crl.pem /etc/openvpn/",
            "chmod 644 /etc/openvpn/crl.pem",
            'echo "CRL updated successfully"',
        ]

        logger.info("Updating Certificate Revocation List")
        self._run_ssm_command(instance_id, " && ".join(commands))

    def _remove_ccd_config(self, instance_id: str, partner_name: str) -> None:
        """Remove client configuration directory entry."""
        commands = [
            "# Remove CCD config for {} (case-insensitive)".format(partner_name),
            f"rm -f /etc/openvpn/ccd/{shlex.quote(partner_name)}",
            f"rm -f /etc/openvpn/ccd/{shlex.quote(partner_name.lower())}",
            f"rm -f /etc/openvpn/ccd/{shlex.quote(partner_name.upper())}",
            "# Find and remove any case variations",
            f"find /etc/openvpn/ccd/ -iname {shlex.quote(partner_name)} -delete 2>/dev/null || true",
            'echo "CCD config for {} removed"'.format(partner_name),
        ]

        logger.info(f"Removing CCD configuration for partner: {partner_name}")
        try:
            self._run_ssm_command(instance_id, " && ".join(commands))
        except Exception as e:
            console.print("[yellow]⚠️ Warning: Could not remove CCD config[/yellow]")
            logger.warning(f"Could not remove CCD config: {e}")

    def _cleanup_certificate_files(self, instance_id: str, partner_name: str) -> None:
        """Clean up certificate files from server."""
        commands = [
            "rm -f /etc/openvpn/{}.ovpn".format(shlex.quote(partner_name)),
            'echo "Certificate files for {} cleaned up"'.format(partner_name),
        ]

        logger.info(f"Cleaning up certificate files for partner: {partner_name}")
        try:
            self._run_ssm_command(instance_id, " && ".join(commands))
        except Exception as e:
            console.print("[yellow]⚠️ Warning: Could not clean up certificate files[/yellow]")
            logger.warning(f"Could not clean up certificate files: {e}")

    def _run_ssm_command(self, instance_id: str, command: str) -> Dict[str, Any]:
        """Run command on instance via SSM."""
        ssm = boto3.client("ssm")

        logger.debug(f"Running SSM command on {instance_id}: {command[:100]}...")

        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]},
        )

        command_id = response["Command"]["CommandId"]
        logger.debug(f"SSM command ID: {command_id}")

        # Wait for command completion
        for i in range(SSM_COMMAND_MAX_ATTEMPTS):
            time.sleep(SSM_COMMAND_POLL_INTERVAL)

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

        raise Exception(
            f"Command {command_id} timed out after {SSM_COMMAND_TIMEOUT_SECONDS} seconds"
        )
