# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Release Dedicated Host Command implementation."""

import argparse
from datetime import datetime, timezone
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger
from telco_cli.utils.prompts import confirm_destructive_operation

logger = get_logger(__name__)


class ReleaseDedicatedHostCommand(BaseCommand):
    """Release a dedicated host assignment."""

    @property
    def name(self) -> str:
        return "release-dedicated-host"

    @property
    def description(self) -> str:
        return "Release a dedicated host assignment"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--host-id", required=True, help="Dedicated host ID to release")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force release even if instances are running on the host",
        )
        parser.add_argument(
            "--deallocate", action="store_true", help="Also remove RAM resource share (if exists)"
        )
        parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    def run(self, args: argparse.Namespace) -> None:
        """Execute the release dedicated host command."""
        try:
            logger.info(f"Releasing dedicated host: {args.host_id}")
            result = self._release_dedicated_host(args)
            console.print(result)

        except TelcoCLIException:
            raise
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            raise TelcoCLIException(ErrorCode.USER_CANCELLED, "Operation cancelled by user")
        except Exception as e:
            logger.exception("Unexpected error during host release")
            raise TelcoCLIException(ErrorCode.HOST_RELEASE_FAILED, str(e))

    def _release_dedicated_host(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Release the dedicated host assignment."""
        try:
            # Validate host ID format
            if not args.host_id.startswith("h-") or len(args.host_id) != 19:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    f"Invalid host ID format '{args.host_id}'. Host IDs should start with 'h-' and be 19 characters long (e.g., h-0123456789abcdef0)",
                )

            ec2_client = boto3.client("ec2")

            # Get host information
            response = ec2_client.describe_hosts(HostIds=[args.host_id])

            if not response["Hosts"]:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR, f"Dedicated host {args.host_id} not found"
                )

            host = response["Hosts"][0]

            # Get current assignment information for confirmation
            current_tags = {tag["Key"]: tag["Value"] for tag in host.get("Tags", [])}
            assigned_to = current_tags.get("AssignedTo", "Unknown")
            partner = current_tags.get("Partner")
            running_instances = len(host.get("Instances", []))

            # Confirmation prompt for destructive operation
            if not args.yes:
                action = "deallocate" if args.deallocate else "release"
                details = [
                    f"Currently assigned to: {assigned_to}",
                    f"Partner: {partner}",
                    f"Running instances: {running_instances}",
                ]
                if args.deallocate:
                    details.append("This will also remove RAM resource shares")

                confirm_destructive_operation(
                    operation_name=action,
                    resource_name=f"dedicated host {args.host_id}",
                    details=details,
                    skip_confirmation=False,
                    raise_on_cancel=True,
                )

            console.print("\nVerifying current host state...")
            recheck_response = ec2_client.describe_hosts(HostIds=[args.host_id])

            if not recheck_response["Hosts"]:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    f"Dedicated host {args.host_id} not found. It may have been deleted.",
                )

            recheck_host = recheck_response["Hosts"][0]
            recheck_tags = {tag["Key"]: tag["Value"] for tag in recheck_host.get("Tags", [])}
            recheck_running_instances = len(recheck_host.get("Instances", []))

            # Check if host has running instances
            if recheck_running_instances > 0 and not args.force:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    f"Host {args.host_id} currently has {recheck_running_instances} running instances. Use --force to release anyway",
                )

            # Remove assignment tags
            tags_to_remove = ["AssignedTo", "AssignedAt", "Partner"]
            existing_tags_to_remove = [tag for tag in tags_to_remove if tag in recheck_tags]

            if existing_tags_to_remove:
                # Delete the assignment tags
                ec2_client.delete_tags(
                    Resources=[args.host_id], Tags=[{"Key": tag} for tag in existing_tags_to_remove]
                )

            # Handle RAM deallocation if requested
            deallocation_result = None
            if args.deallocate:
                deallocation_result = self._deallocate_host_from_account(args.host_id)

            # Add release information
            release_tags = [
                {"Key": "ReleasedAt", "Value": datetime.now(timezone.utc).isoformat()},
                {"Key": "ReleasedBy", "Value": "telcocli"},
            ]

            ec2_client.create_tags(Resources=[args.host_id], Tags=release_tags)

            # Get updated host information
            updated_response = ec2_client.describe_hosts(HostIds=[args.host_id])
            updated_host = updated_response["Hosts"][0]

            result = {
                "Success": True,
                "Release": {
                    "HostId": args.host_id,
                    "InstanceType": updated_host.get("HostProperties", {}).get(
                        "InstanceType", "Unknown"
                    ),
                    "AvailabilityZone": updated_host["AvailabilityZone"],
                    "State": updated_host["State"],
                    "PreviouslyAssignedTo": assigned_to,
                    "PreviousPartner": partner,
                    "ReleasedAt": datetime.now(timezone.utc).isoformat(),
                    "TotalCapacity": updated_host.get("HostProperties", {}).get("TotalVCpus", 0),
                    "AvailableCapacity": updated_host.get("AvailableCapacity", {}).get(
                        "AvailableVCpus", 0
                    ),
                    "RunningInstances": len(updated_host.get("Instances", [])),
                    "Tags": {tag["Key"]: tag["Value"] for tag in updated_host.get("Tags", [])},
                    "TagsOnly": not args.deallocate,
                },
                "Message": f"Successfully {'deallocated' if args.deallocate else 'released'} host {args.host_id} from {assigned_to}",
            }

            if deallocation_result:
                result["Deallocation"] = deallocation_result

            return result

        except ClientError as e:
            logger.error(f"AWS API error: {e.response['Error']['Message']}")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, e.response["Error"]["Message"])
        except TelcoCLIException:
            raise
        except Exception as e:
            logger.exception("Unexpected error during host release")
            raise TelcoCLIException(ErrorCode.HOST_RELEASE_FAILED, str(e))

    def _deallocate_host_from_account(self, host_id: str) -> Dict[str, Any]:
        """Remove RAM resource share for the dedicated host."""
        try:
            ram_client = boto3.client("ram")

            # Find resource shares for this host
            response = ram_client.get_resource_shares(resourceOwner="SELF")

            deleted_shares = []
            for share in response.get("resourceShares", []):
                if f"telcocli-host-{host_id}" in share["name"]:
                    try:
                        ram_client.delete_resource_share(resourceShareArn=share["arn"])
                        deleted_shares.append(share["name"])
                    except ClientError as e:
                        logger.warning(f"Failed to delete resource share {share['name']}: {e}")
                        continue

            if deleted_shares:
                return {
                    "Success": True,
                    "DeletedShares": deleted_shares,
                    "Message": f"Deleted {len(deleted_shares)} RAM resource shares",
                }
            else:
                return {"Success": True, "Message": "No RAM resource shares found for this host"}

        except ClientError as e:
            return {
                "Success": False,
                "Error": f"RAM deallocation failed: {e.response['Error']['Message']}",
            }
        except Exception as e:
            return {"Success": False, "Error": f"Deallocation error: {str(e)}"}
