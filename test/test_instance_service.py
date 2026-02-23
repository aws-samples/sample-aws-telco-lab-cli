"""Tests for Instance Service."""

from unittest.mock import patch

import pytest

from telco_cli.services.instance_service import InstanceService


class TestInstanceService:
    """Test cases for InstanceService."""

    @pytest.fixture
    def service(self):
        with (
            patch("telco_cli.services.instance_service.SSMService"),
            patch("telco_cli.services.instance_service.EC2Service"),
        ):
            return InstanceService()

    def test_list_managed_instances_name_priority(self, service):
        """Test that SSM ComputerName is preferred over EC2 Name tag."""
        mock_instances = [
            {"InstanceId": "i-1234567890abcdef0", "ComputerName": "web-server-prod-01"},
            {"InstanceId": "i-0987654321fedcba0", "ComputerName": None},
            {"InstanceId": "mi-1234567890abcdef0", "ComputerName": "hybrid-server-01"},
            {"InstanceId": "mi-0987654321fedcba0", "ComputerName": None},
        ]

        mock_tags = {
            "i-1234567890abcdef0": {"Name": "WebServer"},
            "i-0987654321fedcba0": {"Name": "DatabaseServer"},
        }

        with patch.object(
            service.ssm_service, "list_managed_instances", return_value=mock_instances.copy()
        ):
            with patch.object(service.ec2_service, "get_instance_tags", return_value=mock_tags):
                result = service.list_managed_instances()

        # Verify naming priority: SSM ComputerName > EC2 Name tag > InstanceId
        assert result[0]["Name"] == "web-server-prod-01"  # SSM preferred over EC2 tag
        assert result[1]["Name"] == "DatabaseServer"  # EC2 tag when no SSM name
        assert result[2]["Name"] == "hybrid-server-01"  # SSM name for non-EC2
        assert result[3]["Name"] == "mi-0987654321fedcba0"  # InstanceId fallback
