"""Tests for GetOutpostUtilizationSummaryCommand."""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.commands.get_outpost_utilization_summary import GetOutpostUtilizationSummaryCommand


class TestGetOutpostUtilizationSummaryCommand:
    """Test cases for GetOutpostUtilizationSummaryCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return GetOutpostUtilizationSummaryCommand()

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.region_filter = None
        args.outpost_id = None
        args.output = "table"
        return args

    def test_command_properties(self, command):
        """Test command properties."""
        assert command.name == "get-outpost-utilization-summary"
        assert "utilization summary" in command.description.lower()

    @patch("telco_cli.commands.get_outpost_utilization_summary.boto3.client")
    def test_get_utilization_summary_success(self, mock_boto3):
        """Test successful utilization summary."""
        # Mock AWS clients
        mock_outposts_client = Mock()
        mock_ec2_client = Mock()
        mock_boto3.side_effect = [mock_outposts_client, mock_ec2_client]

        # Mock outposts paginator
        mock_outposts_paginator = Mock()
        mock_outposts_client.get_paginator.return_value = mock_outposts_paginator
        mock_outposts_paginator.paginate.return_value = [
            {
                "Outposts": [
                    {
                        "OutpostId": "op-123456789",
                        "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                        "Name": "TestOutpost",
                        "AvailabilityZone": "us-west-2a",
                    }
                ]
            }
        ]

        # Mock EC2 hosts paginator
        mock_ec2_paginator = Mock()
        mock_ec2_client.get_paginator.return_value = mock_ec2_paginator
        mock_ec2_paginator.paginate.return_value = [
            {
                "Hosts": [
                    {
                        "HostId": "h-123",
                        "InstanceType": "m5.large",
                        "State": "available",
                        "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                        "InstanceCapacity": 2,
                        "AvailableCapacity": 2,
                        "Tags": [],
                    },
                    {
                        "HostId": "h-456",
                        "InstanceType": "m5.large",
                        "State": "available",
                        "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                        "InstanceCapacity": 2,
                        "AvailableCapacity": 0,
                        "Tags": [{"Key": "AssignedTo", "Value": "partner1"}],
                    },
                ]
            }
        ]

        command = GetOutpostUtilizationSummaryCommand()
        mock_args = Mock()
        mock_args.region_filter = None
        mock_args.outpost_id = None
        mock_args.output = "table"

        result = command._get_utilization_summary(mock_args)

        assert result["Success"] is True

    @patch("telco_cli.commands.get_outpost_utilization_summary.boto3.client")
    def test_get_utilization_summary_aws_error(self, mock_boto3):
        """Test AWS error handling."""
        mock_outposts_client = Mock()
        mock_boto3.return_value = mock_outposts_client

        # Mock ClientError
        mock_outposts_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "ListOutposts"
        )

        command = GetOutpostUtilizationSummaryCommand()
        mock_args = Mock()
        mock_args.region_filter = None
        mock_args.outpost_id = None
        mock_args.output = "table"

        result = command._get_utilization_summary(mock_args)

        assert result["Success"] is False
        assert "Access denied" in str(result["Error"])
