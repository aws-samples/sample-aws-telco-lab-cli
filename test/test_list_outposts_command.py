"""Unit tests for ListOutpostsCommand."""

from argparse import Namespace
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from telco_cli.commands.list_outposts import ListOutpostsCommand


class TestListOutpostsCommand:
    """Test cases for ListOutpostsCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = ListOutpostsCommand()
        self.mock_args = Namespace(
            region_filter=None, status_filter=None, include_capacity=False, output="json"
        )

    def test_command_properties(self):
        """Test command name and description."""
        assert self.command.name == "list-outposts"
        assert "List all AWS Outposts" in self.command.description

    @patch("telco_cli.commands.list_outposts.boto3.client")
    def test_list_outposts_success(self, mock_boto3):
        """Test successful outpost listing."""
        # Mock AWS clients
        mock_outposts_client = Mock()
        mock_ec2_client = Mock()
        mock_boto3.side_effect = [mock_outposts_client, mock_ec2_client]

        # Mock paginator
        mock_paginator = Mock()
        mock_outposts_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Outposts": [
                    {
                        "OutpostId": "op-123456789",
                        "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                        "Name": "TestOutpost",
                        "Description": "Test outpost",
                        "LifeCycleStatus": "ACTIVE",
                        "AvailabilityZone": "us-west-2a",
                        "AvailabilityZoneId": "usw2-az1",
                        "SiteId": "os-123456789",
                        "SiteArn": "arn:aws:outposts:us-west-2:123456789012:site/os-123456789",
                        "SupportedHardwareType": "RACK",
                        "Tags": [],
                    }
                ]
            }
        ]

        # Mock EC2 describe_hosts
        mock_ec2_client.describe_hosts.return_value = {
            "Hosts": [
                {
                    "HostId": "h-123456789",
                    "InstanceType": "m5.large",
                    "State": "available",
                    "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                    "Tags": [],
                }
            ]
        }

        result = self.command._list_outposts(self.mock_args)

        assert result["Success"] is True
        assert len(result["Outposts"]) == 1
        assert result["Outposts"][0]["OutpostId"] == "op-123456789"
        assert result["Summary"]["TotalOutposts"] == 1

    @patch("telco_cli.commands.list_outposts.boto3.client")
    def test_list_outposts_with_filters(self, mock_boto3):
        """Test outpost listing with filters."""
        # Mock AWS clients
        mock_outposts_client = Mock()
        mock_ec2_client = Mock()
        mock_boto3.side_effect = [mock_outposts_client, mock_ec2_client]

        # Set up filters
        self.mock_args.region_filter = "us-west-2"
        self.mock_args.status_filter = "ACTIVE"

        # Mock paginator with multiple outposts
        mock_paginator = Mock()
        mock_outposts_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Outposts": [
                    {
                        "OutpostId": "op-123456789",
                        "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                        "Name": "TestOutpost1",
                        "LifeCycleStatus": "ACTIVE",
                        "AvailabilityZone": "us-west-2a",
                        "AvailabilityZoneId": "usw2-az1",
                        "SiteId": "os-123456789",
                        "SiteArn": "arn:aws:outposts:us-west-2:123456789012:site/os-123456789",
                        "SupportedHardwareType": "RACK",
                        "Tags": [],
                    },
                    {
                        "OutpostId": "op-987654321",
                        "OutpostArn": "arn:aws:outposts:us-east-1:123456789012:outpost/op-987654321",
                        "Name": "TestOutpost2",
                        "LifeCycleStatus": "INACTIVE",
                        "AvailabilityZone": "us-east-1a",
                        "AvailabilityZoneId": "use1-az1",
                        "SiteId": "os-987654321",
                        "SiteArn": "arn:aws:outposts:us-east-1:123456789012:site/os-987654321",
                        "SupportedHardwareType": "RACK",
                        "Tags": [],
                    },
                ]
            }
        ]

        mock_ec2_client.describe_hosts.return_value = {"Hosts": []}

        result = self.command._list_outposts(self.mock_args)

        # Should only include us-west-2 ACTIVE outpost
        assert result["Success"] is True
        assert len(result["Outposts"]) == 1
        assert result["Outposts"][0]["OutpostId"] == "op-123456789"

    @patch("telco_cli.commands.list_outposts.boto3.client")
    def test_list_outposts_aws_error(self, mock_boto3):
        """Test AWS error handling."""
        mock_outposts_client = Mock()
        mock_boto3.return_value = mock_outposts_client

        # Mock ClientError
        mock_outposts_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "ListOutposts"
        )

        result = self.command._list_outposts(self.mock_args)

        assert result["Success"] is False
        assert "Access denied" in result["Error"]["Message"]

    def test_safe_get_int(self):
        """Test _safe_get_int method."""
        assert self.command._safe_get_int(5) == 5
        assert self.command._safe_get_int([1, 2, 3]) == 3
        assert self.command._safe_get_int({"a": 1, "b": 2}) == 2
        assert self.command._safe_get_int("string") == 0
        assert self.command._safe_get_int(None) == 0

    @patch("telco_cli.commands.list_outposts.boto3.client")
    def test_get_outpost_capacity(self, mock_boto3):
        """Test _get_outpost_capacity method."""
        mock_outposts_client = Mock()
        mock_boto3.return_value = mock_outposts_client

        mock_outposts_client.get_outpost_instance_types.return_value = {
            "InstanceTypes": [{"InstanceType": "m5.large"}, {"InstanceType": "c5.xlarge"}]
        }

        result = self.command._get_outpost_capacity(mock_outposts_client, None, "op-123")

        assert result["InstanceTypeCount"] == 2
        assert "m5.large" in result["SupportedInstanceTypes"]
        assert "c5.xlarge" in result["SupportedInstanceTypes"]

    @patch("telco_cli.commands.list_outposts.boto3.client")
    def test_get_outpost_hosts_info(self, mock_boto3):
        """Test _get_outpost_hosts_info method."""
        mock_ec2_client = Mock()
        mock_boto3.return_value = mock_ec2_client

        mock_ec2_client.describe_hosts.return_value = {
            "Hosts": [
                {"HostId": "h-123", "InstanceType": "m5.large", "State": "available", "Tags": []},
                {
                    "HostId": "h-456",
                    "InstanceType": "m5.large",
                    "State": "available",
                    "Tags": [{"Key": "AssignedTo", "Value": "partner1"}],
                },
            ]
        }

        result = self.command._get_outpost_hosts_info(
            mock_ec2_client, "arn:aws:outposts:us-west-2:123456789012:outpost/op-123"
        )

        assert result["TotalHosts"] == 2
        assert result["AvailableHosts"] == 2  # Both hosts have state 'available'
        assert result["AssignedHosts"] == 1  # Only h-456 has AssignedTo tag

    def test_generate_outpost_summary_empty(self):
        """Test _generate_outpost_summary with empty list."""
        result = self.command._generate_outpost_summary([])
        assert result == {}

    def test_generate_outpost_summary_with_data(self):
        """Test _generate_outpost_summary with data."""
        outposts = [
            {
                "LifeCycleStatus": "ACTIVE",
                "AvailabilityZone": "us-west-2a",
                "DedicatedHosts": {"TotalHosts": 5, "AvailableHosts": 3, "AssignedHosts": 2},
            },
            {
                "LifeCycleStatus": "ACTIVE",
                "AvailabilityZone": "us-west-2b",
                "DedicatedHosts": {"TotalHosts": 3, "AvailableHosts": 1, "AssignedHosts": 2},
            },
        ]

        result = self.command._generate_outpost_summary(outposts)

        assert result["TotalOutposts"] == 2
        assert result["TotalDedicatedHosts"] == 8
        assert result["AvailableDedicatedHosts"] == 4
        assert result["AssignedDedicatedHosts"] == 4
        assert result["HostUtilization"] == 50.0
        assert "us-west-2" in result["ByRegion"]
        assert result["ByRegion"]["us-west-2"] == 2

    def test_print_table_format_success(self):
        """Test _print_table_format with successful result."""
        command = ListOutpostsCommand()

        # Mock the console instance
        with patch.object(command, "console") as mock_console:
            result = {
                "Success": True,
                "Outposts": [
                    {
                        "OutpostId": "op-123",
                        "Name": "TestOutpost",
                        "LifeCycleStatus": "ACTIVE",
                        "AvailabilityZone": "us-west-2a",
                        "DedicatedHosts": {"TotalHosts": 5, "AvailableHosts": 3},
                    }
                ],
                "Summary": {
                    "TotalOutposts": 1,
                    "TotalDedicatedHosts": 5,
                    "AvailableDedicatedHosts": 3,
                },
            }

            command._print_table_format(result)

            # Verify console.print was called
            assert mock_console.print.called

    def test_print_table_format_error(self):
        """Test _print_table_format with error result."""
        command = ListOutpostsCommand()

        # Mock the console instance
        with patch.object(command, "console") as mock_console:
            result = {"Success": False, "Error": {"Message": "Test error message"}}

            command._print_table_format(result)

            # Verify console.print was called with error message
            mock_console.print.assert_called_with("❌ Error: Test error message", style="bold red")

    def test_print_summary_format(self):
        """Test _print_summary_format method."""
        command = ListOutpostsCommand()

        # Mock the console instance
        with patch.object(command, "console") as mock_console:
            result = {
                "Success": True,
                "Summary": {
                    "TotalOutposts": 2,
                    "TotalDedicatedHosts": 10,
                    "ByStatus": {"ACTIVE": 2},
                    "ByRegion": {"us-west-2": 2},
                    "HostUtilization": 60.0,
                },
            }

            command._print_summary_format(result)

            # Verify console.print was called
            assert mock_console.print.called
