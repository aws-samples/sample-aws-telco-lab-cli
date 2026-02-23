"""Tests for the create-vpn command."""

import argparse
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError

from telco_cli.commands.vpn import CreateVPNCommand


class TestCreateVPNCommand:
    """Test cases for CreateVPNCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = CreateVPNCommand()

    def test_name_property(self):
        """Test that the command name is correct."""
        assert self.command.name == "create-vpn"

    def test_description_property(self):
        """Test that the command description is correct."""
        assert self.command.description == "Generate VPN certificates for partner access"

    def test_register_arguments(self):
        """Test that command arguments are registered correctly."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # When
        args = parser.parse_args(
            ["test-partner", "--allowed-subnets", "192.168.1.0/24,10.0.0.0/16"]
        )

        # Then
        assert args.partner_name == "test-partner"
        assert args.allowed_subnets == "192.168.1.0/24,10.0.0.0/16"
        assert args.certificate_duration == "30d"  # default value
        assert args.output_dir == "."  # default value

    def test_validate_inputs_valid_partner_name(self):
        """Test validation with valid partner name."""
        # Should not raise any exception
        self.command._validate_inputs("test-partner", "192.168.1.0/24", "30d")
        self.command._validate_inputs("test_partner", "192.168.1.0/24", "30d")
        self.command._validate_inputs("test123", "192.168.1.0/24", "30d")

    def test_validate_inputs_invalid_partner_name(self):
        """Test validation with invalid partner name."""
        with pytest.raises(ValueError, match="Partner name must contain only alphanumeric"):
            self.command._validate_inputs("test partner", "192.168.1.0/24", "30d")

        with pytest.raises(ValueError, match="Partner name must contain only alphanumeric"):
            self.command._validate_inputs("test@partner", "192.168.1.0/24", "30d")

    def test_validate_inputs_valid_subnets(self):
        """Test validation with valid subnet formats."""

        self.command._validate_inputs("test", "192.168.1.0/24", "30d")
        self.command._validate_inputs("test", "192.168.1.0/24,10.0.0.0/16", "30d")
        self.command._validate_inputs("test", "192.168.1.1", "30d")
        self.command._validate_inputs("test", "192.168.1.1,10.0.0.1", "30d")

    def test_validate_inputs_invalid_subnets(self):
        """Test validation with invalid subnet formats."""
        with pytest.raises(ValueError, match="Allowed subnets are required"):
            self.command._validate_inputs("test", "", "30d")

        with pytest.raises(ValueError, match="Invalid CIDR notation"):
            self.command._validate_inputs("test", "192.168.1.0/33", "30d")

        with pytest.raises(ValueError, match="Invalid IP address"):
            self.command._validate_inputs("test", "256.256.256.256/24", "30d")

        with pytest.raises(ValueError, match="Invalid IP address"):
            self.command._validate_inputs("test", "192.168.1", "30d")

    def test_validate_inputs_valid_certificate_duration(self):
        """Test validation with valid certificate duration."""
        # Should not raise any exception
        self.command._validate_inputs("test", "192.168.1.0/24", "30d")
        self.command._validate_inputs("test", "192.168.1.0/24", "365d")
        self.command._validate_inputs("test", "192.168.1.0/24", "1d")

    def test_validate_inputs_invalid_certificate_duration(self):
        """Test validation with invalid certificate duration."""
        with pytest.raises(ValueError, match="Certificate duration must be in format"):
            self.command._validate_inputs("test", "192.168.1.0/24", "30")

        with pytest.raises(ValueError, match="Certificate duration must be in format"):
            self.command._validate_inputs("test", "192.168.1.0/24", "30days")

    def test_is_valid_ip_address(self):
        """Test IP address validation."""
        assert self.command._is_valid_ip_address("192.168.1.1") is True
        assert self.command._is_valid_ip_address("10.0.0.1") is True
        assert self.command._is_valid_ip_address("0.0.0.0") is True
        assert self.command._is_valid_ip_address("255.255.255.255") is True

        assert self.command._is_valid_ip_address("256.1.1.1") is False
        assert self.command._is_valid_ip_address("192.168.1") is False
        assert self.command._is_valid_ip_address("192.168.1.1.1") is False
        assert self.command._is_valid_ip_address("not.an.ip.address") is False

    def test_cidr_to_netmask(self):
        """Test CIDR to netmask conversion."""
        assert self.command._cidr_to_netmask(24) == "255.255.255.0"
        assert self.command._cidr_to_netmask(16) == "255.255.0.0"
        assert self.command._cidr_to_netmask(8) == "255.0.0.0"
        assert self.command._cidr_to_netmask(32) == "255.255.255.255"
        assert self.command._cidr_to_netmask(0) == "0.0.0.0"

    @patch("boto3.client")
    def test_initialize_aws_clients_success(self, mock_boto3_client):
        """Test successful AWS client initialization."""
        mock_ec2_client = Mock()
        mock_ssm_client = Mock()
        mock_boto3_client.side_effect = [mock_ec2_client, mock_ssm_client]

        self.command._initialize_aws_clients()

        assert self.command.ec2_client == mock_ec2_client
        assert self.command.ssm_client == mock_ssm_client
        assert mock_boto3_client.call_count == 2

    @patch("boto3.client")
    def test_initialize_aws_clients_failure(self, mock_boto3_client):
        """Test AWS client initialization failure."""
        mock_boto3_client.side_effect = Exception("AWS initialization failed")

        with pytest.raises(Exception, match="Failed to initialize AWS clients"):
            self.command._initialize_aws_clients()

    @patch("boto3.client")
    def test_discover_openvpn_server_success(self, mock_boto3_client):
        """Test successful OpenVPN server discovery."""
        mock_ec2_client = Mock()
        mock_boto3_client.return_value = mock_ec2_client

        # Mock EC2 response
        mock_response = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "PublicIpAddress": "1.2.3.4",
                            "PublicDnsName": "ec2-1-2-3-4.compute-1.amazonaws.com",
                            "PrivateIpAddress": "10.0.0.1",
                            "PrivateDnsName": "ip-10-0-0-1.ec2.internal",
                            "Tags": [{"Key": "Name", "Value": "test-openvpn-server"}],
                        }
                    ]
                }
            ]
        }
        mock_ec2_client.describe_instances.return_value = mock_response

        self.command.ec2_client = mock_ec2_client
        result = self.command._discover_openvpn_server()

        assert result is not None
        assert result["instance_id"] == "i-1234567890abcdef0"
        assert result["name"] == "test-openvpn-server"
        assert result["endpoint"] == "ec2-1-2-3-4.compute-1.amazonaws.com"
        assert result["port"] == 1194

    @patch("boto3.client")
    def test_discover_openvpn_server_not_found(self, mock_boto3_client):
        """Test OpenVPN server discovery when no servers found."""
        mock_ec2_client = Mock()
        mock_boto3_client.return_value = mock_ec2_client

        # Mock empty EC2 response
        mock_response = {"Reservations": []}
        mock_ec2_client.describe_instances.return_value = mock_response

        self.command.ec2_client = mock_ec2_client
        result = self.command._discover_openvpn_server()

        assert result is None

    @patch("boto3.client")
    def test_check_ssm_connectivity_online(self, mock_boto3_client):
        """Test SSM connectivity check when instance is online."""
        mock_ssm_client = Mock()
        mock_boto3_client.return_value = mock_ssm_client

        # Mock SSM response
        mock_response = {"InstanceInformationList": [{"PingStatus": "Online"}]}
        mock_ssm_client.describe_instance_information.return_value = mock_response

        self.command.ssm_client = mock_ssm_client
        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        assert result is True

    @patch("boto3.client")
    def test_check_ssm_connectivity_offline(self, mock_boto3_client):
        """Test SSM connectivity check when instance is offline."""
        mock_ssm_client = Mock()
        mock_boto3_client.return_value = mock_ssm_client

        # Mock SSM response
        mock_response = {"InstanceInformationList": [{"PingStatus": "ConnectionLost"}]}
        mock_ssm_client.describe_instance_information.return_value = mock_response

        self.command.ssm_client = mock_ssm_client
        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        assert result is False

    @patch("boto3.client")
    @patch("time.sleep")
    def test_run_ssm_command_success(self, mock_sleep, mock_boto3_client):
        """Test successful SSM command execution."""
        mock_ssm_client = Mock()
        mock_boto3_client.return_value = mock_ssm_client

        # Mock SSM send_command response
        mock_send_response = {"Command": {"CommandId": "cmd-1234567890abcdef0"}}
        mock_ssm_client.send_command.return_value = mock_send_response

        # Mock SSM get_command_invocation response
        mock_get_response = {
            "Status": "Success",
            "StandardOutputContent": "Command executed successfully",
        }
        mock_ssm_client.get_command_invocation.return_value = mock_get_response

        self.command.ssm_client = mock_ssm_client
        result = self.command._run_ssm_command("i-1234567890abcdef0", 'echo "test"')

        assert result == mock_get_response
        mock_sleep.assert_called_once_with(5)

    @patch("boto3.client")
    @patch("time.sleep")
    def test_run_ssm_command_failure(self, mock_sleep, mock_boto3_client):
        """Test SSM command execution failure."""
        mock_ssm_client = Mock()
        mock_boto3_client.return_value = mock_ssm_client

        # Mock SSM send_command response
        mock_send_response = {"Command": {"CommandId": "cmd-1234567890abcdef0"}}
        mock_ssm_client.send_command.return_value = mock_send_response

        # Mock SSM get_command_invocation response with failure
        mock_get_response = {
            "Status": "Failed",
            "StandardErrorContent": "Command failed",
            "StandardOutputContent": "",
            "StatusDetails": "Exit code 1",
        }
        mock_ssm_client.get_command_invocation.return_value = mock_get_response

        self.command.ssm_client = mock_ssm_client

        with pytest.raises(Exception, match="SSM command failed with status Failed"):
            self.command._run_ssm_command("i-1234567890abcdef0", "false")

    def test_format_ssm_error(self):
        """Test SSM error formatting."""
        result = {
            "StandardErrorContent": "Error message",
            "StandardOutputContent": "Output message",
            "StatusDetails": "Status details",
        }

        formatted = self.command._format_ssm_error(result)
        expected = "Error: Error message | Output: Output message | Details: Status details"
        assert formatted == expected

    @patch("sys.exit")
    @patch("boto3.client")
    def test_run_no_credentials_error(self, mock_boto3_client, mock_exit):
        """Test run method with no credentials error."""
        mock_boto3_client.side_effect = NoCredentialsError()

        args = argparse.Namespace(
            partner_name="test-partner",
            allowed_subnets="192.168.1.0/24",
            certificate_duration="30d",
            output_dir=".",
        )

        with patch("builtins.print") as mock_print:
            self.command.run(args)

        mock_print.assert_called()
        mock_exit.assert_called_with(1)

    @patch("sys.exit")
    @patch("boto3.client")
    def test_run_client_error(self, mock_boto3_client, mock_exit):
        """Test run method with AWS client error."""
        error_response = {
            "Error": {"Code": "InvalidClientTokenId", "Message": "Invalid credentials"}
        }
        mock_boto3_client.side_effect = ClientError(error_response, "DescribeInstances")

        args = argparse.Namespace(
            partner_name="test-partner",
            allowed_subnets="192.168.1.0/24",
            certificate_duration="30d",
            output_dir=".",
        )

        with patch("builtins.print") as mock_print:
            self.command.run(args)

        mock_print.assert_called()
        mock_exit.assert_called_with(1)

    def test_generate_certificate(self):
        with patch.object(self.command, "_run_ssm_command") as mock_ssm:
            mock_ssm.return_value = {"Status": "Success"}

            self.command._generate_certificate("i-1234567890abcdef0", "test-partner")
            mock_ssm.assert_called_once()
            call_args = mock_ssm.call_args[0]
            assert "test-partner" in call_args[1]

    def test_create_routing_config(self):
        with (
            patch.object(self.command, "_run_ssm_command") as mock_ssm,
            patch.object(self.command, "_cidr_to_netmask") as mock_netmask,
        ):
            mock_ssm.return_value = {"Status": "Success"}
            mock_netmask.return_value = "255.255.255.0"
            self.command._create_routing_config(
                "i-1234567890abcdef0", "test-partner", "192.168.1.0/24,10.0.0.0/16"
            )
            assert mock_ssm.call_count >= 1
            assert mock_netmask.call_count >= 1

    def test_generate_ovpn_file(self):
        server_info = {
            "name": "test-server",
            "instance_id": "i-1234567890abcdef0",
            "endpoint": "vpn.example.com",
            "port": "1194",
            "protocol": "udp",
            "cipher": "AES-256-GCM",
            "auth": "SHA256",
        }

        with patch.object(self.command, "_run_ssm_command") as mock_ssm:
            mock_ssm.return_value = {"Status": "Success"}

            self.command._generate_ovpn_file(server_info, "test-partner")
            mock_ssm.assert_called_once()

    def test_download_ovpn_file(self):
        with patch.object(self.command, "_run_ssm_command") as mock_ssm:
            mock_ssm.return_value = {
                "Status": "Success",
                "StandardOutputContent": "client\ndev tun\nproto udp\n",
            }

            content = self.command._download_ovpn_file("i-1234567890abcdef0", "test-partner")
            assert "client" in content
            mock_ssm.assert_called_once()

    def test_save_ovpn_file_success(self):
        content = "client\ndev tun\nproto udp\n"

        import os

        output_dir = os.getcwd()
        file_path = self.command._save_ovpn_file("test-partner", content, output_dir)
        assert file_path
        assert "test-partner" in file_path
        assert file_path.endswith(".ovpn")
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_save_ovpn_file_permission_error(self):
        content = "client\ndev tun\nproto udp\n"

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(Exception) as exc_info:
                self.command._save_ovpn_file("test-partner", content, "/invalid/path")

            assert "Failed to save VPN configuration file" in str(exc_info.value)

    def test_restart_openvpn_server_success(self):
        with patch.object(self.command, "_run_ssm_command") as mock_ssm:
            mock_ssm.return_value = {"Status": "Success"}

            self.command._restart_openvpn_server("i-1234567890abcdef0")

            mock_ssm.assert_called_once()
            call_args = mock_ssm.call_args[0]
            assert "systemctl restart openvpn" in call_args[1]

    def test_restart_openvpn_server_failure(self):
        with (
            patch.object(self.command, "_run_ssm_command") as mock_ssm,
            patch("telco_cli.commands.vpn.create_vpn.console") as mock_console,
        ):
            mock_ssm.side_effect = Exception("Restart failed")

            self.command._restart_openvpn_server("i-1234567890abcdef0")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Warning: OpenVPN server restart may have failed" in call_args
            warning_call = [
                call for call in mock_console.print.call_args_list if "Warning" in str(call)
            ]
            assert len(warning_call) > 0

    @pytest.mark.parametrize(
        "bits,expected",
        [
            (24, "255.255.255.0"),
            (16, "255.255.0.0"),
            (8, "255.0.0.0"),
            (32, "255.255.255.255"),
            (0, "0.0.0.0"),
        ],
    )
    def test_cidr_to_netmask_parametrized(self, bits, expected):
        result = self.command._cidr_to_netmask(bits)
        assert result == expected

    def test_run_full_flow_success(self):
        args = Mock()
        args.partner_name = "test-partner"
        args.allowed_subnets = "192.168.1.0/24"
        args.certificate_duration = "30d"
        args.output_dir = "/tmp"

        server_info = {
            "name": "test-server",
            "instance_id": "i-1234567890abcdef0",
            "endpoint": "vpn.example.com",
            "port": "1194",
        }

        with (
            patch.object(self.command, "_initialize_aws_clients"),
            patch.object(self.command, "_validate_inputs"),
            patch.object(self.command, "_discover_openvpn_server", return_value=server_info),
            patch.object(self.command, "_check_ssm_connectivity", return_value=True),
            patch.object(self.command, "_generate_certificate"),
            patch.object(self.command, "_create_routing_config"),
            patch.object(self.command, "_generate_ovpn_file"),
            patch.object(self.command, "_download_ovpn_file", return_value="ovpn content"),
            patch.object(self.command, "_save_ovpn_file", return_value="/tmp/test-partner.ovpn"),
            patch.object(self.command, "_restart_openvpn_server"),
            patch("telco_cli.commands.vpn.create_vpn.console"),
        ):

            self.command.run(args)

    def test_run_no_server_found(self):
        args = Mock()
        args.partner_name = "test-partner"
        args.allowed_subnets = "192.168.1.0/24"
        args.certificate_duration = "30d"

        with (
            patch.object(self.command, "_initialize_aws_clients"),
            patch.object(self.command, "_validate_inputs"),
            patch.object(self.command, "_discover_openvpn_server", return_value=None),
            patch("telco_cli.commands.vpn.create_vpn.console_error") as mock_error,
            patch("sys.exit") as mock_exit,
        ):

            self.command.run(args)
            mock_error.print.assert_called()
            mock_exit.assert_called_with(1)

    def test_run_ssm_connectivity_failed(self):
        args = Mock()
        args.partner_name = "test-partner"
        args.allowed_subnets = "192.168.1.0/24"
        args.certificate_duration = "30d"

        server_info = {"instance_id": "i-1234567890abcdef0"}

        with (
            patch.object(self.command, "_initialize_aws_clients"),
            patch.object(self.command, "_validate_inputs"),
            patch.object(self.command, "_discover_openvpn_server", return_value=server_info),
            patch.object(self.command, "_check_ssm_connectivity", return_value=False),
            patch("telco_cli.commands.vpn.create_vpn.console_error") as mock_error,
            patch("sys.exit") as mock_exit,
        ):

            self.command.run(args)
            mock_error.print.assert_called()
            mock_exit.assert_called_with(1)

    def test_save_ovpn_file_empty_content(self):
        """Test save_ovpn_file with empty content."""
        import os

        with pytest.raises(Exception) as exc_info:
            self.command._save_ovpn_file("test-partner", "", os.getcwd())
        assert "VPN configuration content is empty" in str(exc_info.value)

    def test_save_ovpn_file_whitespace_only_content(self):
        """Test save_ovpn_file with whitespace-only content."""
        import os

        with pytest.raises(Exception) as exc_info:
            self.command._save_ovpn_file("test-partner", "   \n\t  ", os.getcwd())
        assert "VPN configuration content is empty" in str(exc_info.value)

    def test_save_ovpn_file_invalid_output_directory(self):
        """Test save_ovpn_file with invalid output directory."""
        with pytest.raises(Exception) as exc_info:
            self.command._save_ovpn_file("test-partner", "content", "/etc/passwd")
        assert "Invalid output directory" in str(exc_info.value)

    def test_save_ovpn_file_path_traversal_protection(self):
        """Test save_ovpn_file protects against path traversal."""
        with pytest.raises(Exception) as exc_info:
            self.command._save_ovpn_file("test-partner", "content", "../../../etc")
        assert "Invalid output directory" in str(exc_info.value)

    @patch("pathlib.Path.write_text")
    def test_save_ovpn_file_write_failure(self, mock_write_text):
        """Test save_ovpn_file when file write fails."""
        mock_write_text.side_effect = OSError("Write failed")

        with pytest.raises(Exception, match="Failed to save VPN configuration file"):
            self.command._save_ovpn_file("test-partner", "content", "/tmp")

    def test_discover_openvpn_server_client_error_handling(self):
        """Test discover_openvpn_server with various ClientError scenarios."""
        with patch("boto3.client") as mock_boto3:
            mock_ec2 = Mock()
            mock_boto3.return_value = mock_ec2

            # Test with specific ClientError
            error_response = {
                "Error": {"Code": "UnauthorizedOperation", "Message": "Access denied"}
            }
            mock_ec2.describe_instances.side_effect = ClientError(
                error_response, "DescribeInstances"
            )

            self.command.ec2_client = mock_ec2

            with pytest.raises(Exception, match="Failed to discover OpenVPN servers"):
                self.command._discover_openvpn_server()

    def test_discover_openvpn_server_fallback_to_ip(self):
        """Test discover_openvpn_server falls back to IP when DNS is empty."""
        with patch("boto3.client") as mock_boto3:
            mock_ec2 = Mock()
            mock_boto3.return_value = mock_ec2

            mock_response = {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-1234567890abcdef0",
                                "PublicIpAddress": "1.2.3.4",
                                "PublicDnsName": "",  # Empty DNS name
                                "PrivateIpAddress": "10.0.0.1",
                                "PrivateDnsName": "ip-10-0-0-1.ec2.internal",
                                "Tags": [{"Key": "Name", "Value": "test-openvpn-server"}],
                            }
                        ]
                    }
                ]
            }
            mock_ec2.describe_instances.return_value = mock_response

            self.command.ec2_client = mock_ec2
            result = self.command._discover_openvpn_server()

            assert result["endpoint"] == "1.2.3.4"

    def test_discover_openvpn_server_no_tags(self):
        """Test discover_openvpn_server with instance that has no tags."""
        with patch("boto3.client") as mock_boto3:
            mock_ec2 = Mock()
            mock_boto3.return_value = mock_ec2

            mock_response = {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-1234567890abcdef0",
                                "PublicIpAddress": "1.2.3.4",
                                "PublicDnsName": "ec2-1-2-3-4.compute-1.amazonaws.com",
                                "Tags": [],  # No tags
                            }
                        ]
                    }
                ]
            }
            mock_ec2.describe_instances.return_value = mock_response

            self.command.ec2_client = mock_ec2
            result = self.command._discover_openvpn_server()

            assert result["name"] == "Unknown"

    def test_check_ssm_connectivity_no_instance_info(self):
        """Test check_ssm_connectivity when no instance information is found."""
        with patch("boto3.client") as mock_boto3:
            mock_ssm = Mock()
            mock_boto3.return_value = mock_ssm

            mock_ssm.describe_instance_information.return_value = {"InstanceInformationList": []}

            self.command.ssm_client = mock_ssm
            result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

            assert result is False

    def test_check_ssm_connectivity_client_error(self):
        """Test check_ssm_connectivity with ClientError."""
        with patch("boto3.client") as mock_boto3:
            mock_ssm = Mock()
            mock_boto3.return_value = mock_ssm

            error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
            mock_ssm.describe_instance_information.side_effect = ClientError(
                error_response, "DescribeInstanceInformation"
            )

            self.command.ssm_client = mock_ssm
            result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

            assert result is False

    def test_format_ssm_error_partial_content(self):
        """Test _format_ssm_error with partial content."""
        # Test with only error content
        result_error_only = {"StandardErrorContent": "Error occurred"}
        formatted = self.command._format_ssm_error(result_error_only)
        assert formatted == "Error: Error occurred"

        # Test with only output content
        result_output_only = {"StandardOutputContent": "Some output"}
        formatted = self.command._format_ssm_error(result_output_only)
        assert formatted == "Output: Some output"

        # Test with only status details
        result_status_only = {"StatusDetails": "Status info"}
        formatted = self.command._format_ssm_error(result_status_only)
        assert formatted == "Details: Status info"

        # Test with empty result
        result_empty = {}
        formatted = self.command._format_ssm_error(result_empty)
        assert formatted == "Unknown error"

    def test_validate_inputs_edge_cases(self):
        """Test _validate_inputs with various edge cases."""
        # Test CIDR with boundary values
        self.command._validate_inputs("test", "0.0.0.0/0", "30d")  # Should pass
        self.command._validate_inputs("test", "255.255.255.255/32", "30d")  # Should pass

        # Test mixed IP and CIDR formats
        self.command._validate_inputs("test", "192.168.1.1,10.0.0.0/16", "30d")

        # Test certificate duration edge cases
        self.command._validate_inputs("test", "192.168.1.0/24", "1d")  # Minimum
        self.command._validate_inputs("test", "192.168.1.0/24", "9999d")  # Large number

    def test_validate_inputs_invalid_cidr_edge_cases(self):
        """Test _validate_inputs with invalid CIDR edge cases."""
        with pytest.raises(ValueError, match="Invalid CIDR notation"):
            self.command._validate_inputs("test", "192.168.1.0/-1", "30d")

        with pytest.raises(ValueError, match="Invalid CIDR notation"):
            self.command._validate_inputs("test", "192.168.1.0/abc", "30d")

    def test_is_valid_ip_address_edge_cases(self):
        """Test _is_valid_ip_address with edge cases."""
        # Test boundary values
        assert self.command._is_valid_ip_address("0.0.0.0") is True
        assert self.command._is_valid_ip_address("255.255.255.255") is True

        # Test invalid cases
        assert self.command._is_valid_ip_address("256.0.0.0") is False
        assert self.command._is_valid_ip_address("192.168.1") is False
        assert self.command._is_valid_ip_address("192.168.1.1.1") is False
        assert self.command._is_valid_ip_address("") is False
        assert self.command._is_valid_ip_address("abc.def.ghi.jkl") is False

    def test_cidr_to_netmask_edge_cases(self):
        """Test _cidr_to_netmask with edge cases."""
        # Test all possible CIDR values
        test_cases = [
            (0, "0.0.0.0"),
            (1, "128.0.0.0"),
            (7, "254.0.0.0"),
            (15, "255.254.0.0"),
            (23, "255.255.254.0"),
            (31, "255.255.255.254"),
            (32, "255.255.255.255"),
        ]

        for bits, expected in test_cases:
            result = self.command._cidr_to_netmask(bits)
            assert result == expected, f"Failed for CIDR /{bits}"
