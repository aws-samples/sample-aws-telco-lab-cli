# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""EC2 service for instance management."""

from typing import Dict, List

import boto3
from botocore.exceptions import ClientError

from telco_cli.utils import get_logger

logger = get_logger(__name__)


class EC2Service:
    """Service for AWS EC2 operations."""

    def __init__(self):
        """Initialize the EC2 service."""
        self.ec2_client = boto3.client("ec2")

    def get_instance_tags(self, instance_ids: List[str]) -> Dict[str, Dict[str, str]]:
        """Get tags for multiple instances."""
        if not instance_ids:
            return {}

        # Filter to only EC2 instance IDs (starting with 'i-')
        ec2_instance_ids = [id for id in instance_ids if id.startswith("i-")]

        if not ec2_instance_ids:
            return {}

        try:
            response = self.ec2_client.describe_instances(InstanceIds=ec2_instance_ids)

            instance_tags = {}
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
                    instance_tags[instance_id] = tags

            return instance_tags

        except ClientError as e:
            logger.warning(f"Failed to get instance tags: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Unexpected error getting instance tags: {e}")
            return {}
