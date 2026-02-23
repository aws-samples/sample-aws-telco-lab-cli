# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Assign Dedicated Host Command implementation."""

import argparse
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger

logger = get_logger(__name__)


class AssignDedicatedHostCommand(BaseCommand):
    """Assign a dedicated host to a partner or account."""

    @property
    def name(self) -> str:
        return "assign-dedicated-host"

    @property
    def description(self) -> str:
        return "Assign a dedicated host to a partner or account"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--host-id", required=True, help="Dedicated host ID to assign")
        parser.add_argument("--partner-name", help="Name of the partner to assign the host to")
        parser.add_argument(
            "--account-id",
            help="AWS account ID to assign the host to (alternative to partner-name)",
        )
        parser.add_argument(
            "--force", action="store_true", help="Force assignment even if host is already assigned"
        )
        parser.add_argument(
            "--enable-ram-sharing",
            action="store_true",
            help="Enable RAM sharing to actually grant access to target account",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the assign dedicated host command."""
        try:
            if not args.partner_name and not args.account_id:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    "Either --partner-name or --account-id must be specified",
                )

            result = self._assign_dedicated_host(args)
            console.print_json(data=result)

        except TelcoCLIException:
            raise
        except ClientError as e:
            logger.error(f"AWS API error: {e.response['Error']['Message']}")
            raise TelcoCLIException(
                ErrorCode.AWS_SERVICE_ERROR, f"AWS error: {e.response['Error']['Message']}"
            )
        except Exception as e:
            logger.exception("Unexpected error during host assignment")
            raise TelcoCLIException(ErrorCode.AWS_SERVICE_ERROR, str(e))

    def _assign_dedicated_host(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Assign the dedicated host to the specified partner or account."""
        try:
            ec2_client = boto3.client("ec2")

            # Get host information
            response = ec2_client.describe_hosts(HostIds=[args.host_id])

            if not response["Hosts"]:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR, f"Dedicated host {args.host_id} not found"
                )

            host = response["Hosts"][0]

            # Check if host is already assigned
            if host["State"] != "available" and not args.force:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    f"Host {args.host_id} is in state '{host['State']}' and not available for assignment",
                )

            # Determine target account
            target_account = args.account_id
            if args.partner_name and not target_account:
                # Look up partner account ID
                target_account = self._get_partner_account_id(args.partner_name)
                if not target_account:
                    raise TelcoCLIException(
                        ErrorCode.VALIDATION_ERROR, f"Partner '{args.partner_name}' not found"
                    )

            console.print("\nVerifying current host state...")
            recheck_response = ec2_client.describe_hosts(HostIds=[args.host_id])

            if not recheck_response["Hosts"]:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    f"Dedicated host {args.host_id} not found. It may have been deleted.",
                )

            recheck_host = recheck_response["Hosts"][0]

            if recheck_host["State"] != "available" and not args.force:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    f"Host {args.host_id} is currently in state '{recheck_host['State']}' and not available for assignment",
                )

            # Create tags for the assignment
            tags = [
                {"Key": "AssignedTo", "Value": args.partner_name or target_account},
                {"Key": "AssignedAt", "Value": datetime.now().isoformat()},
                {"Key": "ManagedBy", "Value": "telcocli"},
            ]

            if args.partner_name:
                tags.append({"Key": "Partner", "Value": args.partner_name})

            # Apply tags to the host
            ec2_client.create_tags(Resources=[args.host_id], Tags=tags)

            # Share the host via RAM if enabled and account ID is provided
            ram_share_arn = None
            if target_account and args.enable_ram_sharing:
                ram_share_arn = self._create_ram_share(args.host_id, target_account)

            # Get updated host information
            updated_response = ec2_client.describe_hosts(HostIds=[args.host_id])
            updated_host = updated_response["Hosts"][0]

            return {
                "Success": True,
                "Assignment": {
                    "HostId": args.host_id,
                    "InstanceType": updated_host.get("HostProperties", {}).get(
                        "InstanceType", "Unknown"
                    ),
                    "AvailabilityZone": updated_host["AvailabilityZone"],
                    "State": updated_host["State"],
                    "AssignedTo": args.partner_name or target_account,
                    "TargetAccount": target_account,
                    "AssignedAt": datetime.now(timezone.utc).isoformat(),
                    "TotalCapacity": updated_host.get("InstanceCapacity", 0),
                    "AvailableCapacity": updated_host.get("AvailableCapacity", 0),
                    "Tags": {tag["Key"]: tag["Value"] for tag in updated_host.get("Tags", [])},
                    "RAMShareArn": ram_share_arn,
                },
                "Message": f"Successfully assigned{' and shared' if args.enable_ram_sharing else ''} host {args.host_id} to {args.partner_name or target_account}",
            }

        except ClientError as e:
            logger.error(f"AWS API error: {e.response['Error']['Message']}")
            raise TelcoCLIException(
                ErrorCode.AWS_SERVICE_ERROR, f"AWS error: {e.response['Error']['Message']}"
            )

    def _get_partner_account_id(self, partner_name: str) -> Optional[str]:
        """Get the account ID for a partner by looking up in Organizations."""
        try:
            org_client = boto3.client("organizations")

            # List all accounts and find the partner
            paginator = org_client.get_paginator("list_accounts")

            for page in paginator.paginate():
                for account in page["Accounts"]:
                    try:
                        tags_response = org_client.list_tags_for_resource(ResourceId=account["Id"])

                        # Check if this account has the partner tag
                        for tag in tags_response.get("Tags", []):
                            if tag["Key"] == "Partner" and tag["Value"] == partner_name:
                                return account["Id"]

                    except ClientError:
                        continue

            return None

        except Exception:
            return None

    def _create_ram_share(self, host_id: str, target_account: str) -> Optional[str]:
        """Create RAM resource share for the dedicated host."""
        try:
            ram_client = boto3.client("ram")

            # Get current account ID for ARN construction
            sts_client = boto3.client("sts")
            current_account = sts_client.get_caller_identity()["Account"]
            current_region = boto3.Session().region_name or "us-east-1"

            # Construct dedicated host ARN
            host_arn = f"arn:aws:ec2:{current_region}:{current_account}:dedicated-host/{host_id}"

            # Create resource share
            share_name = f"dedicated-host-share-{target_account}-{host_id}"

            response = ram_client.create_resource_share(
                name=share_name, resourceArns=[host_arn], principals=[target_account]
            )

            return response["resourceShare"]["resourceShareArn"]

        except Exception as e:
            # Log error but don't fail the assignment
            console.print(f"⚠️ [yellow]Warning: Failed to create RAM share: {str(e)}[/yellow]")
            return None
