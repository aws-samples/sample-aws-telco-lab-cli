# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Instance service for managing EC2 instances with SSM integration."""

from typing import Any, Dict, List

from telco_cli.services.ec2_service import EC2Service
from telco_cli.services.ssm_service import SSMService
from telco_cli.utils import get_logger

logger = get_logger(__name__)


class InstanceService:
    """Service for managing EC2 instances with SSM integration."""

    def __init__(self):
        """Initialize the instance service."""
        self.ssm_service = SSMService()
        self.ec2_service = EC2Service()

    def list_managed_instances(self, status_filter: str = "All") -> List[Dict[str, Any]]:
        """List SSM managed instances enriched with names from both SSM and EC2."""
        instances = self.ssm_service.list_managed_instances(status_filter)

        if not instances:
            return instances

        # Get EC2 tags only for actual EC2 instances (i-*)
        ec2_instances = [inst for inst in instances if inst["InstanceId"].startswith("i-")]
        instance_tags = {}
        if ec2_instances:
            ec2_instance_ids = [inst["InstanceId"] for inst in ec2_instances]
            instance_tags = self.ec2_service.get_instance_tags(ec2_instance_ids)

        # Set names with preference: SSM ComputerName > EC2 Name tag > InstanceId
        for instance in instances:
            instance_id = instance["InstanceId"]
            ssm_name = instance.get("ComputerName")

            # For EC2 instances, get EC2 Name tag as fallback
            ec2_name = None
            if instance_id.startswith("i-"):
                ec2_name = instance_tags.get(instance_id, {}).get("Name")

            # Prefer SSM ComputerName, fallback to EC2 Name tag (if EC2), then InstanceId
            instance["Name"] = ssm_name or ec2_name or instance_id

        return instances
