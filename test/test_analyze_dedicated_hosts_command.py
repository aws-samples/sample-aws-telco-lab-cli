"""Tests for AnalyzeDedicatedHostsCommand."""

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.commands.analyze_dedicated_hosts import AnalyzeDedicatedHostsCommand
from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode


class TestAnalyzeDedicatedHostsCommand(object):
    """Test cases for AnalyzeDedicatedHostsCommand."""

    def setup_method(self, method):
        """Set up test fixtures."""
        self.command = AnalyzeDedicatedHostsCommand()

    def test_name_property(self):
        """Test that command name is correct."""
        assert self.command.name == "analyze-dedicated-hosts"

    def test_description_property(self):
        """Test that command description is correct."""
        expected = "Analyze dedicated hosts with assignment tracking and filtering options"
        assert self.command.description == expected

    def test_register(self):
        """Test that arguments are registered correctly."""
        parser = MagicMock()
        self.command.register(parser)

        parser.add_argument.assert_any_call("--region", help="AWS region to analyze")
        parser.add_argument.assert_any_call(
            "--all-regions", action="store_true", help="Analyze hosts across all regions"
        )

    def test_add_arguments(self):
        """Test that all arguments are added correctly."""
        parser = argparse.ArgumentParser()
        self.command.add_arguments(parser)

        # Test parsing with all arguments
        args = parser.parse_args(
            [
                "--region",
                "us-west-2",
                "--all-regions",
                "--partner",
                "test-partner",
                "--assigned-only",
                "--outpost-id",
                "op-123456789",
                "--instance-type",
                "m5.large",
                "--state",
                "available",
                "--format",
                "json",
            ]
        )

        assert args.region == "us-west-2"
        assert args.all_regions is True
        assert args.partner == "test-partner"
        assert args.assigned_only is True
        assert args.outpost_id == "op-123456789"
        assert args.instance_type == "m5.large"
        assert args.state == "available"
        assert args.format == "json"

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    @patch("telco_cli.commands.analyze_dedicated_hosts.console")
    @patch("telco_cli.commands.analyze_dedicated_hosts.get_logger")
    def test_execute_single_region_success(self, mock_logger, mock_console, mock_boto3):
        """Test successful execution for single region."""
        # Mock logger
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        # Mock EC2 client
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "AvailabilityZone": "us-west-2a",
                    "State": "available",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [
                        {"Key": "AssignedTo", "Value": "test-partner"},
                        {"Key": "Partner", "Value": "test-partner"},
                    ],
                    "HostRecovery": "off",
                    "AutoPlacement": "off",
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        args = argparse.Namespace(
            region="us-west-2",
            all_regions=False,
            partner=None,
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state=None,
            format="table",
        )

        result = self.command.execute(args)

        assert result == 0
        mock_ec2_client.describe_hosts.assert_called_once()

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    @patch("telco_cli.commands.analyze_dedicated_hosts.console")
    @patch("telco_cli.commands.analyze_dedicated_hosts.get_logger")
    def test_execute_all_regions_success(self, mock_logger, mock_console, mock_boto3):
        """Test successful execution for all regions."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        # Mock EC2 client for regions
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock regions response
        mock_ec2_client.describe_regions.return_value = {
            "Regions": [{"RegionName": "us-west-2"}, {"RegionName": "us-east-1"}]
        }

        # Mock host data
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "AvailabilityZone": "us-west-2a",
                    "State": "available",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [],
                    "HostRecovery": "off",
                    "AutoPlacement": "off",
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        args = argparse.Namespace(
            region=None,
            all_regions=True,
            partner=None,
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state=None,
            format="table",
        )

        result = self.command.execute(args)

        assert result == 0
        # Should call describe_regions once and describe_hosts for each region
        mock_ec2_client.describe_regions.assert_called_once()

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    @patch("telco_cli.commands.analyze_dedicated_hosts.console")
    @patch("telco_cli.commands.analyze_dedicated_hosts.get_logger")
    def test_execute_no_hosts_found(self, mock_logger, mock_console, mock_boto3):
        """Test execution when no hosts are found."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client
        mock_ec2_client.describe_hosts.return_value = {"Hosts": []}

        args = argparse.Namespace(
            region="us-west-2",
            all_regions=False,
            partner=None,
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state=None,
            format="table",
        )

        result = self.command.execute(args)

        assert result == 0
        mock_console.print.assert_called_with(
            "📭 [yellow]No dedicated hosts found matching the criteria.[/yellow]"
        )

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    @patch("telco_cli.commands.analyze_dedicated_hosts.console")
    @patch("telco_cli.commands.analyze_dedicated_hosts.get_logger")
    def test_execute_region_error_continues(self, mock_logger, mock_console, mock_boto3):
        """Test execution continues when region analysis fails."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        # Mock the _analyze_region method to raise an exception but execution should continue
        with patch.object(self.command, "_analyze_region") as mock_analyze:
            mock_analyze.side_effect = Exception("AWS Error")

            args = argparse.Namespace(
                region="us-west-2",
                all_regions=False,
                partner=None,
                assigned_only=False,
                unassigned_only=False,
                outpost_id=None,
                instance_type=None,
                state=None,
                format="table",
            )

            # Should not raise exception, should continue and show no hosts found
            result = self.command.execute(args)

            assert result == 0
            mock_console.print.assert_called_with(
                "📭 [yellow]No dedicated hosts found matching the criteria.[/yellow]"
            )

    def test_apply_filters_partner(self):
        """Test filtering by partner."""
        hosts_data = [
            {"AssignedTo": "partner1", "Partner": "partner1", "IsAssigned": True},
            {"AssignedTo": "partner2", "Partner": "partner2", "IsAssigned": True},
            {"AssignedTo": None, "Partner": None, "IsAssigned": False},
        ]

        args = argparse.Namespace(
            partner="partner1",
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state=None,
        )

        result = self.command._apply_filters(hosts_data, args)

        assert len(result) == 1
        assert result[0]["Partner"] == "partner1"

    def test_apply_filters_assigned_only(self):
        """Test filtering for assigned hosts only."""
        hosts_data = [
            {"IsAssigned": True, "AssignedTo": "partner1"},
            {"IsAssigned": False, "AssignedTo": None},
            {"IsAssigned": True, "AssignedTo": "partner2"},
        ]

        args = argparse.Namespace(
            partner=None,
            assigned_only=True,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state=None,
        )

        result = self.command._apply_filters(hosts_data, args)

        assert len(result) == 2
        assert all(host["IsAssigned"] for host in result)

    def test_apply_filters_unassigned_only(self):
        """Test filtering for unassigned hosts only."""
        hosts_data = [
            {"IsAssigned": True, "AssignedTo": "partner1"},
            {"IsAssigned": False, "AssignedTo": None},
            {"IsAssigned": True, "AssignedTo": "partner2"},
        ]

        args = argparse.Namespace(
            partner=None,
            assigned_only=False,
            unassigned_only=True,
            outpost_id=None,
            instance_type=None,
            state=None,
        )

        result = self.command._apply_filters(hosts_data, args)

        assert len(result) == 1
        assert not result[0]["IsAssigned"]

    def test_apply_filters_instance_type(self):
        """Test filtering by instance type."""
        hosts_data = [
            {"InstanceType": "m5.large"},
            {"InstanceType": "m5.xlarge"},
            {"InstanceType": "m5.large"},
        ]

        args = argparse.Namespace(
            partner=None,
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type="m5.large",
            state=None,
        )

        result = self.command._apply_filters(hosts_data, args)

        assert len(result) == 2
        assert all(host["InstanceType"] == "m5.large" for host in result)

    def test_apply_filters_state(self):
        """Test filtering by state."""
        hosts_data = [{"State": "available"}, {"State": "under-assessment"}, {"State": "available"}]

        args = argparse.Namespace(
            partner=None,
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state="available",
        )

        result = self.command._apply_filters(hosts_data, args)

        assert len(result) == 2
        assert all(host["State"] == "available" for host in result)

    @patch("telco_cli.commands.analyze_dedicated_hosts.console")
    def test_display_json(self, mock_console):
        """Test JSON output display."""
        hosts_data = [{"HostId": "h-123", "Region": "us-west-2"}]

        self.command._display_json(hosts_data)

        expected_json = json.dumps(hosts_data, indent=2, default=str)
        mock_console.print.assert_called_once_with(expected_json)

    @patch("csv.DictWriter")
    @patch("sys.stdout")
    def test_display_csv(self, mock_stdout, mock_dict_writer):
        """Test CSV output display."""
        hosts_data = [{"HostId": "h-123", "Region": "us-west-2", "InstanceType": "m5.large"}]

        mock_writer = MagicMock()
        mock_dict_writer.return_value = mock_writer

        self.command._display_csv(hosts_data)

        mock_dict_writer.assert_called_once()
        mock_writer.writeheader.assert_called_once()
        mock_writer.writerow.assert_called_once()

    @patch("telco_cli.commands.analyze_dedicated_hosts.console")
    def test_display_table(self, mock_console):
        """Test table output display."""
        hosts_data = [
            {
                "HostId": "h-123",
                "Region": "us-west-2",
                "InstanceType": "m5.large",
                "AvailabilityZone": "us-west-2a",
                "State": "available",
                "IsAssigned": True,
                "AssignedTo": "partner1",
                "Partner": "partner1",
                "OutpostId": None,
            }
        ]

        self.command._display_table(hosts_data)

        # Should print table and summary
        assert mock_console.print.call_count >= 2

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    def test_get_all_regions_success(self, mock_boto3):
        """Test successful retrieval of all regions."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client
        mock_ec2_client.describe_regions.return_value = {
            "Regions": [{"RegionName": "us-west-2"}, {"RegionName": "us-east-1"}]
        }

        result = self.command._get_all_regions()

        assert result == ["us-west-2", "us-east-1"]

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    def test_get_all_regions_error(self, mock_boto3):
        """Test error handling in get_all_regions."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client
        mock_ec2_client.describe_regions.side_effect = Exception("AWS Error")

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._get_all_regions()

        assert exc_info.value.error_code == ErrorCode.AWS_SERVICE_ERROR

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    @patch("telco_cli.commands.analyze_dedicated_hosts.get_logger")
    def test_analyze_region_success(self, mock_logger, mock_boto3):
        """Test successful region analysis."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "AvailabilityZone": "us-west-2a",
                    "State": "available",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [{"Key": "Partner", "Value": "test-partner"}],
                    "OutpostArn": "arn:aws:outposts:us-west-2:123456789012:outpost/op-123456789",
                    "HostRecovery": "off",
                    "AutoPlacement": "off",
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        args = argparse.Namespace()
        result = self.command._analyze_region("us-west-2", args)

        assert len(result) == 1
        assert result[0]["HostId"] == "h-1234567890abcdef0"
        assert result[0]["Region"] == "us-west-2"
        assert result[0]["OutpostId"] == "op-123456789"

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    def test_analyze_region_no_hosts(self, mock_boto3):
        """Test region analysis with no hosts."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client
        mock_ec2_client.describe_hosts.return_value = {"Hosts": []}

        args = argparse.Namespace()
        result = self.command._analyze_region("us-west-2", args)

        assert result == []

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    def test_analyze_region_error(self, mock_boto3):
        """Test error handling in analyze_region."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client
        mock_ec2_client.describe_hosts.side_effect = Exception("AWS Error")

        args = argparse.Namespace()

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._analyze_region("us-west-2", args)

        assert exc_info.value.error_code == ErrorCode.AWS_SERVICE_ERROR

    def test_run_calls_execute(self):
        """Test that run method calls execute."""
        args = argparse.Namespace()

        with patch.object(self.command, "execute") as mock_execute:
            self.command.run(args)
            mock_execute.assert_called_once_with(args)

    @patch("telco_cli.commands.analyze_dedicated_hosts.get_logger")
    def test_execute_telcocli_exception_reraised(self, mock_logger):
        """Test that TelcoCLIException is re-raised in execute."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        args = argparse.Namespace(
            region="us-west-2",
            all_regions=False,
            partner=None,
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state=None,
            format="table",
        )

        original_exception = TelcoCLIException(ErrorCode.AWS_SERVICE_ERROR, "AWS error")

        with patch.object(self.command, "_analyze_region", side_effect=original_exception):
            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.execute(args)

            assert exc_info.value is original_exception
            assert exc_info.value.error_code == ErrorCode.AWS_SERVICE_ERROR

    @patch("telco_cli.commands.analyze_dedicated_hosts.boto3")
    @patch("telco_cli.commands.analyze_dedicated_hosts.get_logger")
    def test_execute_client_error(self, mock_logger, mock_boto3):
        """Test ClientError handling in execute."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        error_response = {"Error": {"Code": "UnauthorizedOperation", "Message": "Not authorized"}}
        mock_ec2_client.describe_hosts.side_effect = ClientError(error_response, "DescribeHosts")

        args = argparse.Namespace(
            region="us-west-2",
            all_regions=False,
            partner=None,
            assigned_only=False,
            unassigned_only=False,
            outpost_id=None,
            instance_type=None,
            state=None,
            format="table",
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.execute(args)

        assert exc_info.value.error_code == ErrorCode.AWS_SERVICE_ERROR
        assert "AWS error" in str(exc_info.value)
