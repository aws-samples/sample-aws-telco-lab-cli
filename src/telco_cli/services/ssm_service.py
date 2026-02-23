# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""SSM service for instance management."""

from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

from telco_cli.utils import get_logger

logger = get_logger(__name__)


class SSMService:
    """Service for AWS Systems Manager operations."""

    def __init__(self):
        """Initialize the SSM service."""
        self.ssm_client = boto3.client("ssm")

    def list_managed_instances(self, status_filter: str = "All") -> List[Dict[str, Any]]:
        """List SSM managed instances with optional status filter."""
        try:
            filters = []
            if status_filter != "All":
                filters.append({"Key": "PingStatus", "Values": [status_filter]})

            paginator = self.ssm_client.get_paginator("describe_instance_information")
            instances = []

            for page in paginator.paginate(Filters=filters):
                instances.extend(page["InstanceInformationList"])

            logger.info(f"Found {len(instances)} SSM managed instances")
            return instances

        except ClientError as e:
            logger.error(f"Failed to list SSM instances: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing SSM instances: {e}")
            raise

    def get_managed_instance_names(self, instance_ids: List[str]) -> Dict[str, str]:
        """Get computer names for SSM managed instances from inventory."""
        if not instance_ids:
            return {}

        names = {}
        try:
            # Use describe_instance_information which already has ComputerName
            response = self.ssm_client.describe_instance_information(
                Filters=[{"Key": "InstanceIds", "Values": instance_ids}]
            )

            for instance in response.get("InstanceInformationList", []):
                instance_id = instance.get("InstanceId")
                computer_name = instance.get("ComputerName")
                if computer_name and instance_id:
                    names[instance_id] = computer_name

        except ClientError as e:
            logger.warning(f"Failed to get managed instance names: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error getting managed instance names: {e}")

        return names

    def send_command(self, instance_id: str, command: str, timeout: int = 30) -> str:
        """Send a command to an SSM managed instance and return the output."""
        try:
            # Send the command
            response = self.ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [command]},
                TimeoutSeconds=timeout,
            )

            command_id = response["Command"]["CommandId"]

            # Wait for command completion and get output
            waiter = self.ssm_client.get_waiter("command_executed")
            waiter.wait(
                CommandId=command_id,
                InstanceId=instance_id,
                WaiterConfig={"Delay": 1, "MaxAttempts": timeout},
            )

            # Get command output
            output_response = self.ssm_client.get_command_invocation(
                CommandId=command_id, InstanceId=instance_id
            )

            return output_response.get("StandardOutputContent", "")

        except ClientError as e:
            logger.error(f"Failed to send command to {instance_id}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error sending command to {instance_id}: {e}")
            return ""
