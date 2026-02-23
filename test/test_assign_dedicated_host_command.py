"""Tests for AssignDedicatedHostCommand.

Note: All AWS account IDs and resource IDs in this test file are example/mock values:
- Account IDs: 123456789012, 987654321098
- Resource IDs: h-1234567890abcdef0, i-1234567890abcdef0
These are test fixtures and do not represent real AWS resources.
"""

import argparse
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.commands.assign_dedicated_host import AssignDedicatedHostCommand
from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode


class TestAssignDedicatedHostCommand(object):
    """Test cases for AssignDedicatedHostCommand."""

    def setup_method(self, method):
        """Set up test fixtures."""
        self.command = AssignDedicatedHostCommand()

    def test_name_property(self):
        """Test that command name is correct."""
        assert self.command.name == "assign-dedicated-host"

    def test_description_property(self):
        """Test that command description is correct."""
        expected = "Assign a dedicated host to a partner or account"
        assert self.command.description == expected

    def test_register_arguments(self):
        """Test that arguments are registered correctly."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # Test parsing with all arguments
        args = parser.parse_args(
            [
                "--host-id",
                "h-1234567890abcdef0",
                "--partner-name",
                "test-partner",
                "--account-id",
                "123456789012",
                "--force",
                "--enable-ram-sharing",
            ]
        )

        assert args.host_id == "h-1234567890abcdef0"
        assert args.partner_name == "test-partner"
        assert args.account_id == "123456789012"
        assert args.force is True
        assert args.enable_ram_sharing is True

    def test_run_missing_assignment_target(self):
        """Test running command without partner name or account ID."""
        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name=None,
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.run(args)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
        assert "Either --partner-name or --account-id must be specified" in str(exc_info.value)

    @patch("telco_cli.commands.assign_dedicated_host.console")
    def test_run_success_with_partner(self, mock_console):
        """Test successful run with partner name."""
        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        mock_result = {
            "Success": True,
            "Assignment": {"HostId": "h-1234567890abcdef0", "AssignedTo": "test-partner"},
        }

        with patch.object(self.command, "_assign_dedicated_host") as mock_assign:
            mock_assign.return_value = mock_result

            self.command.run(args)

            mock_assign.assert_called_once_with(args)
            mock_console.print_json.assert_called_once_with(data=mock_result)

    @patch("telco_cli.commands.assign_dedicated_host.console")
    def test_run_success_with_account_id(self, mock_console):
        """Test successful run with account ID."""
        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name=None,
            account_id="123456789012",
            force=False,
            enable_ram_sharing=False,
        )

        mock_result = {
            "Success": True,
            "Assignment": {"HostId": "h-1234567890abcdef0", "AssignedTo": "123456789012"},
        }

        with patch.object(self.command, "_assign_dedicated_host") as mock_assign:
            mock_assign.return_value = mock_result

            self.command.run(args)

            mock_assign.assert_called_once_with(args)
            mock_console.print_json.assert_called_once_with(data=mock_result)

    def test_run_assignment_error(self):
        """Test run with assignment error."""
        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        with patch.object(self.command, "_assign_dedicated_host") as mock_assign:
            mock_assign.side_effect = Exception("Assignment failed")

            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            assert exc_info.value.error_code == ErrorCode.AWS_SERVICE_ERROR
            assert "Assignment failed" in str(exc_info.value)

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_success_with_partner(self, mock_boto3):
        """Test successful host assignment with partner name."""
        # Mock EC2 client
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [],
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        # Mock updated host data after tagging
        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "InstanceCapacity": 96,
                    "AvailableCapacity": 96,
                    "Tags": [
                        {"Key": "AssignedTo", "Value": "test-partner"},
                        {"Key": "Partner", "Value": "test-partner"},
                    ],
                }
            ]
        }
        mock_ec2_client.describe_hosts.side_effect = [
            mock_host_data,
            mock_host_data,
            updated_host_data,
        ]

        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        with patch.object(self.command, "_get_partner_account_id") as mock_get_partner:
            mock_get_partner.return_value = "123456789012"

            result = self.command._assign_dedicated_host(args)

            assert result["Success"] is True
            assert result["Assignment"]["HostId"] == "h-1234567890abcdef0"
            assert result["Assignment"]["AssignedTo"] == "test-partner"
            mock_ec2_client.create_tags.assert_called_once()

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_success_with_account_id(self, mock_boto3):
        """Test successful host assignment with account ID."""
        # Mock EC2 client
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [],
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        # Mock updated host data after tagging
        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "InstanceCapacity": 96,
                    "AvailableCapacity": 96,
                    "Tags": [{"Key": "AssignedTo", "Value": "123456789012"}],
                }
            ]
        }
        mock_ec2_client.describe_hosts.side_effect = [
            mock_host_data,
            mock_host_data,
            updated_host_data,
        ]

        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name=None,
            account_id="123456789012",
            force=False,
            enable_ram_sharing=False,
        )

        result = self.command._assign_dedicated_host(args)

        assert result["Success"] is True
        assert result["Assignment"]["HostId"] == "h-1234567890abcdef0"
        assert result["Assignment"]["AssignedTo"] == "123456789012"
        mock_ec2_client.create_tags.assert_called_once()

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_host_not_found(self, mock_boto3):
        """Test assignment when host is not found."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client
        mock_ec2_client.describe_hosts.return_value = {"Hosts": []}

        args = argparse.Namespace(
            host_id="h-nonexistent",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._assign_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
        assert "not found" in str(exc_info.value)

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_not_available(self, mock_boto3):
        """Test assignment when host is not available."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "under-assessment",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [],
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._assign_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
        assert "not available" in str(exc_info.value)

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_force_assignment(self, mock_boto3):
        """Test force assignment when host is not available."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "under-assessment",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [],
                }
            ]
        }

        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "under-assessment",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "InstanceCapacity": 96,
                    "AvailableCapacity": 96,
                    "Tags": [{"Key": "AssignedTo", "Value": "test-partner"}],
                }
            ]
        }
        mock_ec2_client.describe_hosts.side_effect = [
            mock_host_data,
            mock_host_data,
            updated_host_data,
        ]

        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="test-partner",
            account_id=None,
            force=True,
            enable_ram_sharing=False,
        )

        with patch.object(self.command, "_get_partner_account_id") as mock_get_partner:
            mock_get_partner.return_value = "123456789012"

            result = self.command._assign_dedicated_host(args)

            assert result["Success"] is True

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_partner_not_found(self, mock_boto3):
        """Test assignment when partner is not found."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [],
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="nonexistent-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        with patch.object(self.command, "_get_partner_account_id") as mock_get_partner:
            mock_get_partner.return_value = None

            with pytest.raises(TelcoCLIException) as exc_info:
                self.command._assign_dedicated_host(args)

            assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
            assert "not found" in str(exc_info.value)

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_with_ram_sharing(self, mock_boto3):
        """Test assignment with RAM sharing enabled."""
        # Mock EC2 client
        mock_ec2_client = MagicMock()
        mock_boto3.client.side_effect = lambda service, **kwargs: {
            "ec2": mock_ec2_client,
            "ram": MagicMock(),
            "sts": MagicMock(),
        }[service]

        # Mock host data
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Tags": [],
                }
            ]
        }

        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "InstanceCapacity": 96,
                    "AvailableCapacity": 96,
                    "Tags": [{"Key": "AssignedTo", "Value": "123456789012"}],
                }
            ]
        }
        mock_ec2_client.describe_hosts.side_effect = [
            mock_host_data,
            mock_host_data,
            updated_host_data,
        ]

        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name=None,
            account_id="123456789012",
            force=False,
            enable_ram_sharing=True,
        )

        with patch.object(self.command, "_create_ram_share") as mock_ram_share:
            mock_ram_share.return_value = (
                "arn:aws:ram:us-west-2:123456789012:resource-share/test-share"
            )

            result = self.command._assign_dedicated_host(args)

            assert result["Success"] is True
            assert (
                result["Assignment"]["RAMShareArn"]
                == "arn:aws:ram:us-west-2:123456789012:resource-share/test-share"
            )
            mock_ram_share.assert_called_once_with("h-1234567890abcdef0", "123456789012")

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_assign_dedicated_host_client_error(self, mock_boto3):
        """Test assignment with AWS client error."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        error_response = {"Error": {"Code": "InvalidHostId", "Message": "Invalid host ID"}}
        mock_ec2_client.describe_hosts.side_effect = ClientError(error_response, "DescribeHosts")

        args = argparse.Namespace(
            host_id="h-invalid",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._assign_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.AWS_SERVICE_ERROR
        assert "AWS error" in str(exc_info.value)

    def test_run_telcocli_exception_reraised(self):
        """Test that TelcoCLIException is re-raised in run."""
        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        original_exception = TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Validation error")

        with patch.object(self.command, "_assign_dedicated_host", side_effect=original_exception):
            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            assert exc_info.value is original_exception
            assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    def test_run_client_error(self):
        """Test ClientError handling in run."""
        args = argparse.Namespace(
            host_id="h-1234567890abcdef0",
            partner_name="test-partner",
            account_id=None,
            force=False,
            enable_ram_sharing=False,
        )

        error_response = {"Error": {"Code": "InvalidHostId", "Message": "Invalid host ID"}}

        with patch.object(
            self.command,
            "_assign_dedicated_host",
            side_effect=ClientError(error_response, "DescribeHosts"),
        ):
            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            assert exc_info.value.error_code == ErrorCode.AWS_SERVICE_ERROR
            assert "AWS error" in str(exc_info.value)

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_get_partner_account_id_success(self, mock_boto3):
        """Test successful partner account ID lookup."""
        mock_org_client = MagicMock()
        mock_boto3.client.return_value = mock_org_client

        # Mock paginator
        mock_paginator = MagicMock()
        mock_org_client.get_paginator.return_value = mock_paginator

        # Mock accounts data
        mock_paginator.paginate.return_value = [
            {"Accounts": [{"Id": "123456789012", "Name": "Partner Account"}]}
        ]

        # Mock tags response
        mock_org_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Partner", "Value": "test-partner"}]
        }

        result = self.command._get_partner_account_id("test-partner")

        assert result == "123456789012"

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_get_partner_account_id_not_found(self, mock_boto3):
        """Test partner account ID lookup when not found."""
        mock_org_client = MagicMock()
        mock_boto3.client.return_value = mock_org_client

        # Mock paginator
        mock_paginator = MagicMock()
        mock_org_client.get_paginator.return_value = mock_paginator

        # Mock accounts data
        mock_paginator.paginate.return_value = [
            {"Accounts": [{"Id": "123456789012", "Name": "Other Account"}]}
        ]

        # Mock tags response (no partner tag)
        mock_org_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "production"}]
        }

        result = self.command._get_partner_account_id("nonexistent-partner")

        assert result is None

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    def test_get_partner_account_id_error(self, mock_boto3):
        """Test partner account ID lookup with error."""
        mock_org_client = MagicMock()
        mock_boto3.client.return_value = mock_org_client
        mock_org_client.get_paginator.side_effect = Exception("Organizations error")

        result = self.command._get_partner_account_id("test-partner")

        assert result is None

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    @patch("telco_cli.commands.assign_dedicated_host.console")
    def test_create_ram_share_success(self, mock_console, mock_boto3):
        """Test successful RAM share creation."""
        # Mock clients
        mock_ram_client = MagicMock()
        mock_sts_client = MagicMock()
        mock_session = MagicMock()

        mock_boto3.client.side_effect = lambda service, **kwargs: {
            "ram": mock_ram_client,
            "sts": mock_sts_client,
        }[service]
        mock_boto3.Session.return_value = mock_session
        mock_session.region_name = "us-west-2"

        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock RAM response
        mock_ram_client.create_resource_share.return_value = {
            "resourceShare": {
                "resourceShareArn": "arn:aws:ram:us-west-2:123456789012:resource-share/test-share"
            }
        }

        result = self.command._create_ram_share("h-1234567890abcdef0", "987654321098")

        assert result == "arn:aws:ram:us-west-2:123456789012:resource-share/test-share"
        mock_ram_client.create_resource_share.assert_called_once()

    @patch("telco_cli.commands.assign_dedicated_host.boto3")
    @patch("telco_cli.commands.assign_dedicated_host.console")
    def test_create_ram_share_error(self, mock_console, mock_boto3):
        """Test RAM share creation with error."""
        mock_ram_client = MagicMock()
        mock_boto3.client.return_value = mock_ram_client
        mock_ram_client.create_resource_share.side_effect = Exception("RAM error")

        result = self.command._create_ram_share("h-1234567890abcdef0", "987654321098")

        assert result is None
        mock_console.print.assert_called_once()
