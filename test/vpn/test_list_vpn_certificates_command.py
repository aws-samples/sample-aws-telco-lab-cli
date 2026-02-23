"""Tests for list VPN certificates command."""

import argparse
import unittest
from unittest.mock import Mock, patch

from telco_cli.commands.vpn import ListVPNCertificatesCommand


class TestListVPNCertificatesCommand(unittest.TestCase):
    """Test cases for ListVPNCertificatesCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = ListVPNCertificatesCommand()

    def test_command_properties(self):
        """Test command has correct properties."""
        self.assertEqual(self.command.name, "list-vpn-certificates")
        self.assertEqual(self.command.description, "List active VPN certificates")

    def test_register_arguments(self):
        """Test command registers correct arguments."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # Parse test arguments
        args = parser.parse_args(["--show-details"])
        self.assertTrue(args.show_details)

        args = parser.parse_args([])
        self.assertFalse(args.show_details)

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_discover_openvpn_server_success(self, mock_boto3_client):
        """Test successful OpenVPN server discovery."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "PublicIpAddress": "54.123.45.67",
                            "PublicDnsName": "ec2-54-123-45-67.compute-1.amazonaws.com",
                            "PrivateIpAddress": "10.0.1.100",
                            "PrivateDnsName": "ip-10-0-1-100.ec2.internal",
                            "Tags": [{"Key": "Name", "Value": "lab-ovpn-server"}],
                        }
                    ]
                }
            ]
        }

        result = self.command._discover_openvpn_server()

        self.assertIsNotNone(result)
        self.assertEqual(result["instance_id"], "i-1234567890abcdef0")
        self.assertEqual(result["name"], "lab-ovpn-server")
        self.assertEqual(result["public_ip"], "54.123.45.67")
        self.assertEqual(result["endpoint"], "ec2-54-123-45-67.compute-1.amazonaws.com")

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_discover_openvpn_server_no_dns(self, mock_boto3_client):
        """Test OpenVPN server discovery with no DNS name."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "PublicIpAddress": "54.123.45.67",
                            "PublicDnsName": "",  # Empty DNS name
                            "Tags": [{"Key": "Name", "Value": "vpn-server"}],
                        }
                    ]
                }
            ]
        }

        result = self.command._discover_openvpn_server()

        self.assertIsNotNone(result)
        self.assertEqual(result["endpoint"], "54.123.45.67")  # Falls back to IP

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_discover_openvpn_server_no_name_tag(self, mock_boto3_client):
        """Test OpenVPN server discovery with no Name tag."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "PublicIpAddress": "54.123.45.67",
                            "Tags": [],  # No tags
                        }
                    ]
                }
            ]
        }

        result = self.command._discover_openvpn_server()

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Unknown")  # Default name

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_discover_openvpn_server_not_found(self, mock_boto3_client):
        """Test OpenVPN server not found."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.return_value = {"Reservations": []}

        result = self.command._discover_openvpn_server()

        self.assertIsNone(result)

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_discover_openvpn_server_no_public_ip(self, mock_boto3_client):
        """Test OpenVPN server discovery skips instance without public IP."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            # No PublicIpAddress
                            "Tags": [{"Key": "Name", "Value": "vpn-server"}],
                        }
                    ]
                }
            ]
        }

        result = self.command._discover_openvpn_server()

        self.assertIsNone(result)

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_discover_openvpn_server_aws_credentials_error(self, mock_boto3_client):
        """Test OpenVPN server discovery with AWS credentials error."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.side_effect = Exception("InvalidClientTokenId")

        with self.assertRaises(Exception) as context:
            self.command._discover_openvpn_server()

        self.assertIn("AWS credentials are invalid", str(context.exception))

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_discover_openvpn_server_other_exception(self, mock_boto3_client):
        """Test OpenVPN server discovery continues on non-credential errors."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        # First call fails with non-credential error, rest return empty
        mock_ec2.describe_instances.side_effect = [
            Exception("Some other error"),
            {"Reservations": []},
            {"Reservations": []},
        ]

        result = self.command._discover_openvpn_server()

        self.assertIsNone(result)
        self.assertEqual(mock_ec2.describe_instances.call_count, 3)  # 3 filter sets

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_check_ssm_connectivity_online(self, mock_boto3_client):
        """Test SSM connectivity check when online."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.return_value = {
            "InstanceInformationList": [{"PingStatus": "Online"}]
        }

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertTrue(result)

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_check_ssm_connectivity_offline(self, mock_boto3_client):
        """Test SSM connectivity check when offline."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.return_value = {
            "InstanceInformationList": [{"PingStatus": "Offline"}]
        }

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertFalse(result)

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_check_ssm_connectivity_no_instance_info(self, mock_boto3_client):
        """Test SSM connectivity check with no instance information."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.return_value = {"InstanceInformationList": []}

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertFalse(result)

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    def test_check_ssm_connectivity_exception(self, mock_boto3_client):
        """Test SSM connectivity check with exception."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.side_effect = Exception("SSM error")

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertFalse(result)

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_issued_certificates_success(self, mock_run_ssm):
        """Test getting issued certificates successfully."""
        mock_run_ssm.return_value = {"StandardOutputContent": "partner-nokia\npartner-verizon\n"}

        result = self.command._get_issued_certificates("i-1234567890abcdef0")

        self.assertEqual(result, ["partner-nokia", "partner-verizon"])

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_issued_certificates_no_certificates(self, mock_run_ssm):
        """Test getting issued certificates when none exist."""
        mock_run_ssm.return_value = {"StandardOutputContent": "NO_CERTIFICATES"}

        result = self.command._get_issued_certificates("i-1234567890abcdef0")

        self.assertEqual(result, [])

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_issued_certificates_empty_output(self, mock_run_ssm):
        """Test getting issued certificates with empty output."""
        mock_run_ssm.return_value = {"StandardOutputContent": ""}

        result = self.command._get_issued_certificates("i-1234567890abcdef0")

        self.assertEqual(result, [])

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_certificate_details_success(self, mock_run_ssm):
        """Test getting certificate details successfully."""
        mock_run_ssm.return_value = {
            "StandardOutputContent": """subject=CN = partner-nokia
notBefore=Sep 10 03:48:20 2025 GMT
notAfter=Sep  8 03:48:20 2035 GMT
serial=01"""
        }

        result = self.command._get_certificate_details("i-1234567890abcdef0", ["partner-nokia"])

        self.assertEqual(len(result), 1)
        self.assertIn("partner-nokia", result)
        self.assertEqual(result["partner-nokia"]["SerialNumber"], "01")

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_certificate_details_exception(self, mock_run_ssm):
        """Test getting certificate details with exception."""
        mock_run_ssm.side_effect = Exception("SSM command failed")

        result = self.command._get_certificate_details("i-1234567890abcdef0", ["partner-nokia"])

        self.assertEqual(len(result), 1)
        self.assertIn("partner-nokia", result)
        self.assertEqual(result["partner-nokia"]["Error"], "Could not retrieve certificate details")

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_ccd_configurations_success(self, mock_run_ssm):
        """Test getting CCD configurations successfully."""
        mock_run_ssm.return_value = {
            "StandardOutputContent": """=== partner-nokia ===
push "route 10.0.0.0 255.255.255.0"
push "route 192.168.1.0 255.255.255.0"
=== partner-verizon ===
No routes configured"""
        }

        result = self.command._get_ccd_configurations("i-1234567890abcdef0")

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result["partner-nokia"], ["10.0.0.0 255.255.255.0", "192.168.1.0 255.255.255.0"]
        )
        self.assertEqual(result["partner-verizon"], [])

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_ccd_configurations_no_directory(self, mock_run_ssm):
        """Test getting CCD configurations when directory doesn't exist."""
        mock_run_ssm.return_value = {"StandardOutputContent": "No CCD directory found"}

        result = self.command._get_ccd_configurations("i-1234567890abcdef0")

        self.assertEqual(result, {})

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_ccd_configurations_exception(self, mock_run_ssm):
        """Test getting CCD configurations with exception."""
        mock_run_ssm.side_effect = Exception("SSM command failed")

        result = self.command._get_ccd_configurations("i-1234567890abcdef0")

        self.assertEqual(result, {})

    def test_parse_certificate_details(self):
        """Test parsing certificate details from openssl output."""
        output = """subject=CN = partner-nokia
notBefore=Sep 10 03:48:20 2025 GMT
notAfter=Sep  8 03:48:20 2035 GMT
serial=01"""

        result = self.command._parse_certificate_details(output)

        self.assertEqual(result["Subject"], "CN = partner-nokia")
        self.assertEqual(result["ValidFrom"], "Sep 10 03:48:20 2025 GMT")
        self.assertEqual(result["ValidUntil"], "Sep  8 03:48:20 2035 GMT")
        self.assertEqual(result["SerialNumber"], "01")

    def test_parse_certificate_details_empty(self):
        """Test parsing empty certificate details."""
        output = ""

        result = self.command._parse_certificate_details(output)

        self.assertEqual(result, {})

    def test_parse_ccd_configurations(self):
        """Test parsing CCD configurations."""
        output = """=== partner-nokia ===
push "route 10.0.0.0 255.255.255.0"
push "route 192.168.1.0 255.255.255.0"
=== partner-verizon ===
No routes configured"""

        result = self.command._parse_ccd_configurations(output)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result["partner-nokia"], ["10.0.0.0 255.255.255.0", "192.168.1.0 255.255.255.0"]
        )
        self.assertEqual(result["partner-verizon"], [])

    def test_parse_ccd_configurations_empty(self):
        """Test parsing empty CCD configurations."""
        output = ""

        result = self.command._parse_ccd_configurations(output)

        self.assertEqual(result, {})

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    @patch("telco_cli.commands.vpn.list_vpn_certificates.time.sleep")
    def test_run_ssm_command_success(self, mock_sleep, mock_boto3_client):
        """Test successful SSM command execution."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.send_command.return_value = {"Command": {"CommandId": "cmd-123"}}

        mock_ssm.get_command_invocation.return_value = {
            "Status": "Success",
            "StandardOutputContent": "Command output",
        }

        result = self.command._run_ssm_command("i-1234567890abcdef0", "echo test")

        self.assertEqual(result["Status"], "Success")
        self.assertEqual(result["StandardOutputContent"], "Command output")

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    @patch("telco_cli.commands.vpn.list_vpn_certificates.time.sleep")
    def test_run_ssm_command_failure(self, mock_sleep, mock_boto3_client):
        """Test failed SSM command execution."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.send_command.return_value = {"Command": {"CommandId": "cmd-123"}}

        mock_ssm.get_command_invocation.return_value = {
            "Status": "Failed",
            "StandardErrorContent": "Command failed",
        }

        with self.assertRaises(Exception) as context:
            self.command._run_ssm_command("i-1234567890abcdef0", "echo test")

        self.assertIn("Command failed", str(context.exception))

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    @patch("telco_cli.commands.vpn.list_vpn_certificates.time.sleep")
    def test_run_ssm_command_timeout(self, mock_sleep, mock_boto3_client):
        """Test SSM command timeout."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.send_command.return_value = {"Command": {"CommandId": "cmd-123"}}

        # Always return InProgress status
        mock_ssm.get_command_invocation.return_value = {"Status": "InProgress"}

        with self.assertRaises(Exception) as context:
            self.command._run_ssm_command("i-1234567890abcdef0", "echo test")

        self.assertIn("timed out after 60 seconds", str(context.exception))

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    @patch("telco_cli.commands.vpn.list_vpn_certificates.time.sleep")
    def test_run_ssm_command_invocation_does_not_exist(self, mock_sleep, mock_boto3_client):
        """Test SSM command with InvocationDoesNotExist error."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.send_command.return_value = {"Command": {"CommandId": "cmd-123"}}

        # First call raises InvocationDoesNotExist, then succeeds
        mock_ssm.get_command_invocation.side_effect = [
            Exception("InvocationDoesNotExist"),
            {"Status": "Success", "StandardOutputContent": "Output"},
        ]

        result = self.command._run_ssm_command("i-1234567890abcdef0", "echo test")

        self.assertEqual(result["Status"], "Success")

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    @patch("telco_cli.commands.vpn.list_vpn_certificates.time.sleep")
    def test_run_ssm_command_other_exception(self, mock_sleep, mock_boto3_client):
        """Test SSM command with other exception."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.send_command.return_value = {"Command": {"CommandId": "cmd-123"}}

        mock_ssm.get_command_invocation.side_effect = Exception("Some other error")

        with self.assertRaises(Exception) as context:
            self.command._run_ssm_command("i-1234567890abcdef0", "echo test")

        self.assertIn("Some other error", str(context.exception))

    @patch("telco_cli.commands.vpn.list_vpn_certificates.boto3.client")
    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_no_server_found(self, mock_console_error, mock_boto3_client):
        """Test run when no OpenVPN server is found."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.return_value = {"Reservations": []}

        args = Mock()
        args.show_details = False

        with self.assertRaises(Exception) as context:
            self.command.run(args)

        self.assertIn("No OpenVPN server found", str(context.exception))
        mock_console_error.assert_called()

    @patch.object(ListVPNCertificatesCommand, "_discover_openvpn_server")
    @patch.object(ListVPNCertificatesCommand, "_check_ssm_connectivity")
    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_ssm_not_accessible(self, mock_console_error, mock_check_ssm, mock_discover):
        """Test run when SSM is not accessible."""
        mock_discover.return_value = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-vpn-server",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        mock_check_ssm.return_value = False

        args = Mock()
        args.show_details = False

        with self.assertRaises(Exception) as context:
            self.command.run(args)

        self.assertIn("not accessible via SSM", str(context.exception))
        mock_console_error.assert_called()

    @patch.object(ListVPNCertificatesCommand, "_discover_openvpn_server")
    @patch.object(ListVPNCertificatesCommand, "_check_ssm_connectivity")
    @patch.object(ListVPNCertificatesCommand, "_get_issued_certificates")
    @patch.object(ListVPNCertificatesCommand, "_get_ccd_configurations")
    @patch("telco_cli.utils.logging.console.print")
    def test_run_success_no_certificates(
        self, mock_console_print, mock_get_ccd, mock_get_certs, mock_check_ssm, mock_discover
    ):
        """Test successful run with no certificates."""
        mock_discover.return_value = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-vpn-server",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        mock_check_ssm.return_value = True
        mock_get_certs.return_value = []
        mock_get_ccd.return_value = {}

        args = Mock()
        args.show_details = False

        self.command.run(args)

        # Verify key outputs
        console_calls = [str(call) for call in mock_console_print.call_args_list]
        self.assertTrue(any("No certificates found" in call for call in console_calls))
        self.assertTrue(any("0 active certificate(s)" in call for call in console_calls))

    @patch.object(ListVPNCertificatesCommand, "_discover_openvpn_server")
    @patch.object(ListVPNCertificatesCommand, "_check_ssm_connectivity")
    @patch.object(ListVPNCertificatesCommand, "_get_issued_certificates")
    @patch.object(ListVPNCertificatesCommand, "_get_certificate_details")
    @patch.object(ListVPNCertificatesCommand, "_get_ccd_configurations")
    @patch("telco_cli.utils.logging.console.print")
    def test_run_success_with_certificates(
        self,
        mock_console_print,
        mock_get_ccd,
        mock_get_details,
        mock_get_certs,
        mock_check_ssm,
        mock_discover,
    ):
        """Test successful run with certificates."""
        mock_discover.return_value = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-vpn-server",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        mock_check_ssm.return_value = True
        mock_get_certs.return_value = ["partner-nokia", "partner-verizon"]
        mock_get_details.return_value = {
            "partner-nokia": {
                "ValidFrom": "Sep 10 03:48:20 2025 GMT",
                "ValidUntil": "Sep  8 03:48:20 2035 GMT",
                "SerialNumber": "01",
            }
        }
        mock_get_ccd.return_value = {"partner-nokia": ["10.0.0.0 255.255.255.0"]}

        args = Mock()
        args.show_details = True

        self.command.run(args)

        # Verify key outputs
        console_calls = [str(call) for call in mock_console_print.call_args_list]
        self.assertTrue(any("partner-nokia" in call for call in console_calls))
        self.assertTrue(any("partner-verizon" in call for call in console_calls))
        self.assertTrue(any("2 active certificate(s)" in call for call in console_calls))

    @patch.object(ListVPNCertificatesCommand, "_discover_openvpn_server")
    @patch.object(ListVPNCertificatesCommand, "_check_ssm_connectivity")
    @patch.object(ListVPNCertificatesCommand, "_get_issued_certificates")
    @patch.object(ListVPNCertificatesCommand, "_get_ccd_configurations")
    @patch("telco_cli.utils.logging.console.print")
    def test_run_success_no_details_requested(
        self, mock_console_print, mock_get_ccd, mock_get_certs, mock_check_ssm, mock_discover
    ):
        """Test successful run without certificate details requested."""
        mock_discover.return_value = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-vpn-server",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        mock_check_ssm.return_value = True
        mock_get_certs.return_value = ["partner-nokia"]
        mock_get_ccd.return_value = {}

        args = Mock()
        args.show_details = False  # Details not requested

        self.command.run(args)

        # Verify certificate details were not retrieved
        console_calls = [str(call) for call in mock_console_print.call_args_list]
        self.assertFalse(any("ValidFrom" in call for call in console_calls))
        self.assertFalse(any("ValidUntil" in call for call in console_calls))

    @patch.object(ListVPNCertificatesCommand, "_discover_openvpn_server")
    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_generic_exception(self, mock_console_error, mock_discover):
        """Test run with generic exception."""
        mock_discover.side_effect = Exception("Generic error")

        args = Mock()
        args.show_details = False

        with self.assertRaises(Exception) as context:
            self.command.run(args)

        self.assertIn("Generic error", str(context.exception))
        mock_console_error.assert_called()

    def test_display_certificates_table_with_details(self):
        """Test _display_certificates_table with show_details=True."""
        server_info = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-server",
            "endpoint": "vpn.example.com",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        certificates = ["partner-nokia", "partner-verizon"]
        ccd_configs = {"partner-nokia": ["192.168.1.0 255.255.255.0"]}
        cert_details = {
            "partner-nokia": {
                "ValidFrom": "Sep 10 03:48:20 2025 GMT",
                "ValidUntil": "Sep  8 03:48:20 2035 GMT",
                "SerialNumber": "01",
            }
        }

        # This should not raise an exception
        self.command._display_certificates_table(
            server_info, certificates, ccd_configs, cert_details, True
        )

    def test_display_certificates_table_no_certificates(self):
        """Test _display_certificates_table with no certificates."""
        server_info = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-server",
            "endpoint": "vpn.example.com",
            "port": 1194,
            "network": "10.10.10.0/24",
        }

        # This should not raise an exception
        self.command._display_certificates_table(server_info, [], {}, {}, False)

    def test_display_certificates_json_with_details(self):
        """Test _display_certificates_json with show_details=True."""
        server_info = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-server",
            "endpoint": "vpn.example.com",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        certificates = ["partner-nokia"]
        ccd_configs = {"partner-nokia": ["192.168.1.0 255.255.255.0"]}
        cert_details = {
            "partner-nokia": {
                "ValidFrom": "Sep 10 03:48:20 2025 GMT",
                "ValidUntil": "Sep  8 03:48:20 2035 GMT",
                "SerialNumber": "01",
            }
        }

        # This should not raise an exception
        self.command._display_certificates_json(
            server_info, certificates, ccd_configs, cert_details, True
        )

    def test_display_certificates_json_no_certificates(self):
        """Test _display_certificates_json with no certificates."""
        server_info = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-server",
            "endpoint": "vpn.example.com",
            "port": 1194,
            "network": "10.10.10.0/24",
        }

        # This should not raise an exception
        self.command._display_certificates_json(server_info, [], {}, {}, False)

    @patch.object(ListVPNCertificatesCommand, "_discover_openvpn_server")
    @patch.object(ListVPNCertificatesCommand, "_check_ssm_connectivity")
    @patch.object(ListVPNCertificatesCommand, "_get_issued_certificates")
    @patch.object(ListVPNCertificatesCommand, "_get_ccd_configurations")
    @patch.object(ListVPNCertificatesCommand, "_display_certificates_json")
    def test_run_with_json_output_format(
        self, mock_display_json, mock_get_ccd, mock_get_certs, mock_check_ssm, mock_discover
    ):
        """Test run method with JSON output format."""
        server_info = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-server",
            "endpoint": "vpn.example.com",
            "port": 1194,
            "network": "10.10.10.0/24",
        }

        mock_discover.return_value = server_info
        mock_check_ssm.return_value = True
        mock_get_certs.return_value = []
        mock_get_ccd.return_value = {}

        args = Mock()
        args.show_details = False
        args.output = "json"

        self.command.run(args)
        mock_display_json.assert_called_once()

    @patch.object(ListVPNCertificatesCommand, "_discover_openvpn_server")
    @patch.object(ListVPNCertificatesCommand, "_check_ssm_connectivity")
    @patch.object(ListVPNCertificatesCommand, "_get_issued_certificates")
    @patch.object(ListVPNCertificatesCommand, "_get_ccd_configurations")
    @patch.object(ListVPNCertificatesCommand, "_display_certificates_table")
    def test_run_with_table_output_format(
        self, mock_display_table, mock_get_ccd, mock_get_certs, mock_check_ssm, mock_discover
    ):
        """Test run method with table output format."""
        server_info = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-server",
            "endpoint": "vpn.example.com",
            "port": 1194,
            "network": "10.10.10.0/24",
        }

        mock_discover.return_value = server_info
        mock_check_ssm.return_value = True
        mock_get_certs.return_value = []
        mock_get_ccd.return_value = {}

        args = Mock()
        args.show_details = False
        args.output = "table"

        self.command.run(args)
        mock_display_table.assert_called_once()

    def test_parse_certificate_details_partial_output(self):
        """Test _parse_certificate_details with partial openssl output."""
        # Test with only subject
        output_subject_only = "subject=CN = partner-nokia"
        result = self.command._parse_certificate_details(output_subject_only)
        expected = {"Subject": "CN = partner-nokia"}
        self.assertEqual(result, expected)

        # Test with only dates
        output_dates_only = """notBefore=Sep 10 03:48:20 2025 GMT
notAfter=Sep  8 03:48:20 2035 GMT"""
        result = self.command._parse_certificate_details(output_dates_only)
        expected = {
            "ValidFrom": "Sep 10 03:48:20 2025 GMT",
            "ValidUntil": "Sep  8 03:48:20 2035 GMT",
        }
        self.assertEqual(result, expected)

    def test_parse_ccd_configurations_complex_routes(self):
        """Test _parse_ccd_configurations with complex routing configurations."""
        output = """=== partner-nokia ===
push "route 10.0.0.0 255.255.255.0"
push "route 192.168.1.0 255.255.255.0"
push "route 172.16.0.0 255.240.0.0"
=== partner-verizon ===
push "route 10.10.0.0 255.255.0.0"
=== partner-tmobile ===
No routes configured
=== partner-att ===
push "route 192.168.100.0 255.255.255.0"
"""

        result = self.command._parse_ccd_configurations(output)

        expected = {
            "partner-nokia": [
                "10.0.0.0 255.255.255.0",
                "192.168.1.0 255.255.255.0",
                "172.16.0.0 255.240.0.0",
            ],
            "partner-verizon": ["10.10.0.0 255.255.0.0"],
            "partner-tmobile": [],
            "partner-att": ["192.168.100.0 255.255.255.0"],
        }

        self.assertEqual(result, expected)

    @patch.object(ListVPNCertificatesCommand, "_run_ssm_command")
    def test_get_certificate_details_mixed_results(self, mock_run_ssm):
        """Test _get_certificate_details with mixed success/failure results."""
        cert_names = ["partner-nokia", "partner-verizon", "partner-tmobile"]

        def mock_run_ssm_command(instance_id, command):
            if "partner-nokia" in command:
                return {
                    "StandardOutputContent": """subject=CN = partner-nokia
notBefore=Sep 10 03:48:20 2025 GMT
notAfter=Sep  8 03:48:20 2035 GMT
serial=01"""
                }
            elif "partner-verizon" in command:
                raise Exception("Certificate file not found")
            else:  # partner-tmobile
                return {"StandardOutputContent": "Certificate not found"}

        mock_run_ssm.side_effect = mock_run_ssm_command
        result = self.command._get_certificate_details("i-1234567890abcdef0", cert_names)

        # Nokia should have details
        self.assertIn("partner-nokia", result)
        self.assertEqual(result["partner-nokia"]["SerialNumber"], "01")

        # Verizon should have error
        self.assertIn("partner-verizon", result)
        self.assertEqual(
            result["partner-verizon"]["Error"], "Could not retrieve certificate details"
        )

        # T-Mobile should have empty details (no matching patterns)
        self.assertIn("partner-tmobile", result)


if __name__ == "__main__":
    unittest.main()
