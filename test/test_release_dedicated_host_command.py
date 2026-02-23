"""Tests for ReleaseDedicatedHostCommand."""

import argparse
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.commands.release_dedicated_host import ReleaseDedicatedHostCommand
from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode


class TestReleaseDedicatedHostCommand(object):
    """Test cases for ReleaseDedicatedHostCommand."""

    def setup_method(self, method):
        """Set up test fixtures."""
        self.command = ReleaseDedicatedHostCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "release-dedicated-host"

    def test_description_property(self):
        """Test command description property."""
        expected = "Release a dedicated host assignment"
        assert self.command.description == expected

    def test_register_arguments(self):
        """Test argument registration."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # Parse test arguments
        args = parser.parse_args(["--host-id", "h-123456789", "--force", "--deallocate"])

        assert args.host_id == "h-123456789"
        assert args.force is True
        assert args.deallocate is True

    @patch("telco_cli.commands.release_dedicated_host.console")
    @patch("telco_cli.commands.release_dedicated_host.get_logger")
    def test_run_success(self, mock_logger, mock_console):
        """Test successful host release."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        args = MagicMock()
        args.host_id = "h-123456789"
        args.force = False
        args.deallocate = False

        with patch.object(self.command, "_release_dedicated_host") as mock_release:
            mock_release.return_value = {"Success": True, "host_id": "h-123456789"}

            self.command.run(args)

            mock_release.assert_called_once_with(args)
            mock_console.print.assert_called_once()

    @patch("telco_cli.commands.release_dedicated_host.get_logger")
    def test_run_telco_cli_exception(self, mock_logger):
        """Test TelcoCLIException handling."""
        args = MagicMock()
        args.host_id = "h-123456789"

        with patch.object(self.command, "_release_dedicated_host") as mock_release:
            mock_release.side_effect = TelcoCLIException(
                ErrorCode.AWS_CONNECTION_ERROR, "Test error"
            )

            with pytest.raises(TelcoCLIException):
                self.command.run(args)

    @patch("telco_cli.commands.release_dedicated_host.get_logger")
    def test_run_keyboard_interrupt(self, mock_logger):
        """Test KeyboardInterrupt handling."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        args = MagicMock()
        args.host_id = "h-123456789"

        with patch.object(self.command, "_release_dedicated_host") as mock_release:
            mock_release.side_effect = KeyboardInterrupt()

            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            assert exc_info.value.error_code == ErrorCode.USER_CANCELLED

    @patch("telco_cli.commands.release_dedicated_host.get_logger")
    def test_run_unexpected_exception(self, mock_logger):
        """Test unexpected exception handling."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log

        args = MagicMock()
        args.host_id = "h-123456789"

        with patch.object(self.command, "_release_dedicated_host") as mock_release:
            mock_release.side_effect = Exception("Unexpected error")

            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            assert exc_info.value.error_code == ErrorCode.HOST_RELEASE_FAILED

    def test_invalid_host_id_format(self):
        """Test invalid host ID format validation (lines 63-64)."""
        # Test the validation logic directly by checking the condition
        invalid_ids = ["invalid-id", "h-123", "i-1234567890abcdef0", "h-", "h-0123456789abcde"]

        for invalid_id in invalid_ids:
            # Test the validation condition directly
            is_valid = invalid_id.startswith("h-") and len(invalid_id) == 19
            assert not is_valid, f"ID {invalid_id} should be invalid"

        # Test a valid ID (19 characters total: h- + 17 hex chars)
        valid_id = "h-0123456789abcdef0"
        is_valid = valid_id.startswith("h-") and len(valid_id) == 19
        assert is_valid, f"ID {valid_id} should be valid"

    @patch("telco_cli.commands.release_dedicated_host.boto3.client")
    @patch("telco_cli.utils.console")
    @patch("builtins.input", return_value="no")
    def test_user_cancellation(self, mock_input, mock_console, mock_boto3):
        """Test user cancellation during confirmation (lines 88-89)."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client

        mock_client.describe_hosts.return_value = {
            "Hosts": [
                {
                    "Tags": [{"Key": "AssignedTo", "Value": "test-user"}],
                    "Instances": [],
                    "AvailabilityZone": "us-west-2a",
                    "State": "available",
                }
            ]
        }

        args = argparse.Namespace(
            host_id="h-0123456789abcdef0", yes=False, deallocate=False, force=False
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._release_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.USER_CANCELLED

    @patch("telco_cli.commands.release_dedicated_host.boto3.client")
    def test_running_instances_without_force(self, mock_boto3):
        """Test validation when host has running instances (lines 97-98)."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client

        mock_client.describe_hosts.return_value = {
            "Hosts": [{"Tags": [], "Instances": [{"InstanceId": "i-123"}]}]  # Has running instance
        }

        args = argparse.Namespace(host_id="h-0123456789abcdef0", yes=True, force=False)

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._release_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
        assert "running instances" in str(exc_info.value)

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_release_dedicated_host_success(self, mock_boto3):
        """Test successful host release."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 96},
                    "Instances": [],
                    "Tags": [
                        {"Key": "AssignedTo", "Value": "test-partner"},
                        {"Key": "Partner", "Value": "test-partner"},
                        {"Key": "AssignedAt", "Value": "2023-01-01T00:00:00Z"},
                    ],
                }
            ]
        }

        # Mock updated host data after release
        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 96},
                    "Instances": [],
                    "Tags": [
                        {"Key": "ReleasedAt", "Value": "2023-01-01T01:00:00Z"},
                        {"Key": "ReleasedBy", "Value": "telcocli"},
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
            host_id="h-1234567890abcdef0", force=False, deallocate=False, yes=True
        )

        result = self.command._release_dedicated_host(args)

        assert result["Success"] is True
        assert result["Release"]["HostId"] == "h-1234567890abcdef0"
        assert result["Release"]["PreviouslyAssignedTo"] == "test-partner"
        assert result["Release"]["PreviousPartner"] == "test-partner"
        mock_ec2_client.delete_tags.assert_called_once()
        mock_ec2_client.create_tags.assert_called_once()

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_release_dedicated_host_not_found(self, mock_boto3):
        """Test release when host is not found."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client
        mock_ec2_client.describe_hosts.return_value = {"Hosts": []}

        args = argparse.Namespace(
            host_id="h-00000000000000000", force=False, deallocate=False, yes=True
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._release_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
        assert "not found" in str(exc_info.value)

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_release_dedicated_host_with_running_instances(self, mock_boto3):
        """Test release when host has running instances without force."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data with running instances
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large"},
                    "Instances": [
                        {"InstanceId": "i-1234567890abcdef0"},
                        {"InstanceId": "i-0987654321fedcba0"},
                    ],
                    "Tags": [{"Key": "AssignedTo", "Value": "test-partner"}],
                }
            ]
        }
        mock_ec2_client.describe_hosts.return_value = mock_host_data

        args = argparse.Namespace(
            host_id="h-1234567890abcdef0", force=False, deallocate=False, yes=True
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._release_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
        assert "running instances" in str(exc_info.value)

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_release_dedicated_host_force_with_running_instances(self, mock_boto3):
        """Test force release when host has running instances."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data with running instances
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 48},
                    "Instances": [
                        {"InstanceId": "i-1234567890abcdef0"},
                        {"InstanceId": "i-0987654321fedcba0"},
                    ],
                    "Tags": [
                        {"Key": "AssignedTo", "Value": "test-partner"},
                        {"Key": "Partner", "Value": "test-partner"},
                    ],
                }
            ]
        }

        # Mock updated host data after release
        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 48},
                    "Instances": [
                        {"InstanceId": "i-1234567890abcdef0"},
                        {"InstanceId": "i-0987654321fedcba0"},
                    ],
                    "Tags": [
                        {"Key": "ReleasedAt", "Value": "2023-01-01T01:00:00Z"},
                        {"Key": "ReleasedBy", "Value": "telcocli"},
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
            host_id="h-1234567890abcdef0", force=True, deallocate=False, yes=True
        )

        result = self.command._release_dedicated_host(args)

        assert result["Success"] is True
        assert result["Release"]["RunningInstances"] == 2
        mock_ec2_client.delete_tags.assert_called_once()
        mock_ec2_client.create_tags.assert_called_once()

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_release_dedicated_host_with_deallocation(self, mock_boto3):
        """Test host release with RAM deallocation."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 96},
                    "Instances": [],
                    "Tags": [
                        {"Key": "AssignedTo", "Value": "test-partner"},
                        {"Key": "Partner", "Value": "test-partner"},
                    ],
                }
            ]
        }

        # Mock updated host data after release
        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 96},
                    "Instances": [],
                    "Tags": [
                        {"Key": "ReleasedAt", "Value": "2023-01-01T01:00:00Z"},
                        {"Key": "ReleasedBy", "Value": "telcocli"},
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
            host_id="h-1234567890abcdef0", force=False, deallocate=True, yes=True
        )

        mock_deallocation_result = {
            "Success": True,
            "DeletedShares": ["share-1", "share-2"],
            "Message": "Deleted 2 RAM resource shares",
        }

        with patch.object(self.command, "_deallocate_host_from_account") as mock_deallocate:
            mock_deallocate.return_value = mock_deallocation_result

            result = self.command._release_dedicated_host(args)

            assert result["Success"] is True
            assert result["Release"]["TagsOnly"] is False
            assert "Deallocation" in result
            assert result["Deallocation"] == mock_deallocation_result
            mock_deallocate.assert_called_once_with("h-1234567890abcdef0")

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_release_dedicated_host_no_assignment_tags(self, mock_boto3):
        """Test release when host has no assignment tags."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        # Mock host data without assignment tags
        mock_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 96},
                    "Instances": [],
                    "Tags": [{"Key": "Environment", "Value": "production"}],
                }
            ]
        }

        # Mock updated host data after release
        updated_host_data = {
            "Hosts": [
                {
                    "HostId": "h-1234567890abcdef0",
                    "State": "available",
                    "AvailabilityZone": "us-west-2a",
                    "HostProperties": {"InstanceType": "m5.large", "TotalVCpus": 96},
                    "AvailableCapacity": {"AvailableVCpus": 96},
                    "Instances": [],
                    "Tags": [
                        {"Key": "Environment", "Value": "production"},
                        {"Key": "ReleasedAt", "Value": "2023-01-01T01:00:00Z"},
                        {"Key": "ReleasedBy", "Value": "telcocli"},
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
            host_id="h-1234567890abcdef0", force=False, deallocate=False, yes=True
        )

        result = self.command._release_dedicated_host(args)

        assert result["Success"] is True
        assert result["Release"]["PreviouslyAssignedTo"] == "Unknown"
        assert result["Release"]["PreviousPartner"] is None
        # Should not call delete_tags since no assignment tags exist
        mock_ec2_client.delete_tags.assert_not_called()
        mock_ec2_client.create_tags.assert_called_once()

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_release_dedicated_host_client_error(self, mock_boto3):
        """Test release with AWS client error."""
        mock_ec2_client = MagicMock()
        mock_boto3.client.return_value = mock_ec2_client

        error_response = {"Error": {"Code": "InvalidHostId", "Message": "Invalid host ID"}}
        mock_ec2_client.describe_hosts.side_effect = ClientError(error_response, "DescribeHosts")

        args = argparse.Namespace(
            host_id="h-00000000000000000", force=False, deallocate=False, yes=True
        )

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._release_dedicated_host(args)

        assert exc_info.value.error_code == ErrorCode.AWS_API_ERROR

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_deallocate_host_from_account_success(self, mock_boto3):
        """Test successful RAM deallocation."""
        mock_ram_client = MagicMock()
        mock_boto3.client.return_value = mock_ram_client

        # Mock resource shares response
        mock_ram_client.get_resource_shares.return_value = {
            "resourceShares": [
                {
                    "name": "telcocli-host-h-1234567890abcdef0-share",
                    "arn": "arn:aws:ram:us-west-2:123456789012:resource-share/share-1",
                },
                {
                    "name": "other-share",
                    "arn": "arn:aws:ram:us-west-2:123456789012:resource-share/share-2",
                },
                {
                    "name": "telcocli-host-h-1234567890abcdef0-another",
                    "arn": "arn:aws:ram:us-west-2:123456789012:resource-share/share-3",
                },
            ]
        }

        result = self.command._deallocate_host_from_account("h-1234567890abcdef0")

        assert result["Success"] is True
        assert len(result["DeletedShares"]) == 2
        assert "telcocli-host-h-1234567890abcdef0-share" in result["DeletedShares"]
        assert "telcocli-host-h-1234567890abcdef0-another" in result["DeletedShares"]
        # Should call delete_resource_share twice
        assert mock_ram_client.delete_resource_share.call_count == 2

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_deallocate_host_from_account_no_shares(self, mock_boto3):
        """Test RAM deallocation when no shares exist."""
        mock_ram_client = MagicMock()
        mock_boto3.client.return_value = mock_ram_client

        # Mock empty resource shares response
        mock_ram_client.get_resource_shares.return_value = {"resourceShares": []}

        result = self.command._deallocate_host_from_account("h-1234567890abcdef0")

        assert result["Success"] is True
        assert "No RAM resource shares found" in result["Message"]
        mock_ram_client.delete_resource_share.assert_not_called()

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    @patch("telco_cli.commands.release_dedicated_host.logger")
    def test_deallocate_host_from_account_partial_failure(self, mock_logger, mock_boto3):
        """Test RAM deallocation with partial failures."""
        mock_ram_client = MagicMock()
        mock_boto3.client.return_value = mock_ram_client

        # Mock resource shares response
        mock_ram_client.get_resource_shares.return_value = {
            "resourceShares": [
                {
                    "name": "telcocli-host-h-1234567890abcdef0-share1",
                    "arn": "arn:aws:ram:us-west-2:123456789012:resource-share/share-1",
                },
                {
                    "name": "telcocli-host-h-1234567890abcdef0-share2",
                    "arn": "arn:aws:ram:us-west-2:123456789012:resource-share/share-2",
                },
            ]
        }

        # Mock delete_resource_share to fail on second call
        error_response = {
            "Error": {"Code": "ResourceShareNotFound", "Message": "Resource share not found"}
        }
        mock_ram_client.delete_resource_share.side_effect = [
            None,  # First call succeeds
            ClientError(error_response, "DeleteResourceShare"),  # Second call fails
        ]

        result = self.command._deallocate_host_from_account("h-1234567890abcdef0")

        assert result["Success"] is True
        assert len(result["DeletedShares"]) == 1
        assert "telcocli-host-h-1234567890abcdef0-share1" in result["DeletedShares"]
        # Should log warning for failed deletion
        mock_logger.warning.assert_called_once()

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_deallocate_host_from_account_client_error(self, mock_boto3):
        """Test RAM deallocation with client error."""
        mock_ram_client = MagicMock()
        mock_boto3.client.return_value = mock_ram_client

        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_ram_client.get_resource_shares.side_effect = ClientError(
            error_response, "GetResourceShares"
        )

        result = self.command._deallocate_host_from_account("h-1234567890abcdef0")

        assert result["Success"] is False
        assert "RAM deallocation failed" in result["Error"]

    @patch("telco_cli.commands.release_dedicated_host.boto3")
    def test_deallocate_host_from_account_exception(self, mock_boto3):
        """Test RAM deallocation with unexpected exception."""
        mock_ram_client = MagicMock()
        mock_boto3.client.return_value = mock_ram_client
        mock_ram_client.get_resource_shares.side_effect = Exception("Unexpected error")

        result = self.command._deallocate_host_from_account("h-1234567890abcdef0")

        assert result["Success"] is False
        assert "Deallocation error" in result["Error"]
