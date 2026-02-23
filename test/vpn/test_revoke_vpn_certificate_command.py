"""Tests for revoke VPN certificate command."""

import argparse
import unittest
from unittest.mock import Mock, patch

from telco_cli.commands.vpn import RevokeVPNCertificateCommand


class TestRevokeVPNCertificateCommand(unittest.TestCase):
    """Test cases for RevokeVPNCertificateCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = RevokeVPNCertificateCommand()

    def test_command_properties(self):
        """Test command has correct properties."""
        self.assertEqual(self.command.name, "revoke-vpn-certificate")
        self.assertEqual(self.command.description, "Revoke VPN certificates for a partner")

    def test_register_arguments(self):
        """Test command registers correct arguments."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # Test argument is registered correctly
        args = parser.parse_args(["partner-nokia"])
        self.assertEqual(args.partner_name, "partner-nokia")

        # Test help is available
        with self.assertRaises(SystemExit):
            parser.parse_args(["--help"])

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    def test_discover_openvpn_server_not_found(self, mock_boto3_client):
        """Test OpenVPN server not found."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.return_value = {"Reservations": []}

        result = self.command._discover_openvpn_server()

        self.assertIsNone(result)

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    def test_discover_openvpn_server_aws_credentials_error(self, mock_boto3_client):
        """Test OpenVPN server discovery with AWS credentials error."""
        mock_ec2 = Mock()
        mock_boto3_client.return_value = mock_ec2

        mock_ec2.describe_instances.side_effect = Exception("InvalidClientTokenId")

        with self.assertRaises(Exception) as context:
            self.command._discover_openvpn_server()

        self.assertIn("AWS credentials are invalid", str(context.exception))

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    def test_check_ssm_connectivity_online(self, mock_boto3_client):
        """Test SSM connectivity check when online."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.return_value = {
            "InstanceInformationList": [{"PingStatus": "Online"}]
        }

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertTrue(result)

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    def test_check_ssm_connectivity_offline(self, mock_boto3_client):
        """Test SSM connectivity check when offline."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.return_value = {
            "InstanceInformationList": [{"PingStatus": "Offline"}]
        }

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertFalse(result)

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    def test_check_ssm_connectivity_no_instance_info(self, mock_boto3_client):
        """Test SSM connectivity check with no instance information."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.return_value = {"InstanceInformationList": []}

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertFalse(result)

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    def test_check_ssm_connectivity_exception(self, mock_boto3_client):
        """Test SSM connectivity check with exception."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.describe_instance_information.side_effect = Exception("SSM error")

        result = self.command._check_ssm_connectivity("i-1234567890abcdef0")

        self.assertFalse(result)

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    def test_check_certificate_exists_true(self, mock_run_ssm):
        """Test certificate exists check returns true."""
        mock_run_ssm.return_value = {"StandardOutputContent": "EXISTS"}

        result = self.command._check_certificate_exists("i-1234567890abcdef0", "partner-nokia")

        self.assertTrue(result)

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    def test_check_certificate_exists_false(self, mock_run_ssm):
        """Test certificate exists check returns false."""
        mock_run_ssm.return_value = {"StandardOutputContent": "NOT_FOUND"}

        result = self.command._check_certificate_exists("i-1234567890abcdef0", "partner-nokia")

        self.assertFalse(result)

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    def test_check_certificate_exists_exception(self, mock_run_ssm):
        """Test certificate exists check with exception."""
        mock_run_ssm.side_effect = Exception("SSM command failed")

        result = self.command._check_certificate_exists("i-1234567890abcdef0", "partner-nokia")

        self.assertFalse(result)

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.time.sleep")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.time.sleep")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.time.sleep")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.time.sleep")
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

    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.boto3.client")
    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.time.sleep")
    def test_run_ssm_command_other_exception(self, mock_sleep, mock_boto3_client):
        """Test SSM command with other exception."""
        mock_ssm = Mock()
        mock_boto3_client.return_value = mock_ssm

        mock_ssm.send_command.return_value = {"Command": {"CommandId": "cmd-123"}}

        mock_ssm.get_command_invocation.side_effect = Exception("Some other error")

        with self.assertRaises(Exception) as context:
            self.command._run_ssm_command("i-1234567890abcdef0", "echo test")

        self.assertIn("Some other error", str(context.exception))

    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_invalid_partner_name(self, mock_console_error):
        """Test run with invalid partner name."""
        args = Mock()
        args.partner_name = "partner@invalid!"

        with self.assertRaises(ValueError) as context:
            self.command.run(args)

        self.assertIn("alphanumeric characters", str(context.exception))
        mock_console_error.assert_called()

    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_invalid_partner_name_empty(self, mock_console_error):
        """Test run with empty partner name."""
        args = Mock()
        args.partner_name = ""

        with self.assertRaises(ValueError) as context:
            self.command.run(args)

        self.assertIn("alphanumeric characters", str(context.exception))

    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_no_server_found(self, mock_console_error, mock_discover):
        """Test run when no OpenVPN server is found."""
        mock_discover.return_value = None

        args = Mock()
        args.partner_name = "partner-nokia"

        with self.assertRaises(Exception) as context:
            self.command.run(args)

        self.assertIn("No OpenVPN server found", str(context.exception))
        mock_console_error.assert_called()

    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch.object(RevokeVPNCertificateCommand, "_check_ssm_connectivity")
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
        args.partner_name = "partner-nokia"

        with self.assertRaises(Exception) as context:
            self.command.run(args)

        self.assertIn("not accessible via SSM", str(context.exception))
        mock_console_error.assert_called()

    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch.object(RevokeVPNCertificateCommand, "_check_ssm_connectivity")
    @patch.object(RevokeVPNCertificateCommand, "_check_certificate_exists")
    @patch("telco_cli.utils.logging.console_error.print")
    @patch("telco_cli.utils.logging.console.print")
    def test_run_certificate_not_found(
        self,
        mock_console_print,
        mock_console_error_print,
        mock_check_cert,
        mock_check_ssm,
        mock_discover,
    ):
        """Test run when certificate doesn't exist."""
        mock_discover.return_value = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-vpn-server",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        mock_check_ssm.return_value = True
        mock_check_cert.return_value = False

        args = Mock()
        args.partner_name = "partner-nokia"

        # Should not raise exception, just print error
        self.command.run(args)

        # Verify error message was printed
        console_error_calls = [str(call) for call in mock_console_error_print.call_args_list]
        self.assertTrue(
            any(
                "Certificate for partner 'partner-nokia' not found" in call
                for call in console_error_calls
            )
        )

    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch.object(RevokeVPNCertificateCommand, "_check_ssm_connectivity")
    @patch.object(RevokeVPNCertificateCommand, "_check_certificate_exists")
    @patch.object(RevokeVPNCertificateCommand, "_revoke_certificate")
    @patch.object(RevokeVPNCertificateCommand, "_update_crl")
    @patch.object(RevokeVPNCertificateCommand, "_remove_ccd_config")
    @patch.object(RevokeVPNCertificateCommand, "_cleanup_certificate_files")
    @patch("telco_cli.utils.logging.console.print")
    def test_run_success(
        self,
        mock_console_print,
        mock_cleanup,
        mock_remove_ccd,
        mock_update_crl,
        mock_revoke,
        mock_check_cert,
        mock_check_ssm,
        mock_discover,
    ):
        """Test successful certificate revocation."""
        mock_discover.return_value = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-vpn-server",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        mock_check_ssm.return_value = True
        mock_check_cert.return_value = True

        args = Mock()
        args.partner_name = "partner-nokia"

        self.command.run(args)

        # Verify all steps were called
        mock_revoke.assert_called_once_with("i-1234567890abcdef0", "partner-nokia")
        mock_update_crl.assert_called_once_with("i-1234567890abcdef0")
        mock_remove_ccd.assert_called_once_with("i-1234567890abcdef0", "partner-nokia")
        mock_cleanup.assert_called_once_with("i-1234567890abcdef0", "partner-nokia")

        # Verify success message was printed
        console_calls = [str(call) for call in mock_console_print.call_args_list]
        self.assertTrue(
            any("VPN certificate revoked successfully!" in call for call in console_calls)
        )
        self.assertTrue(any("partner-nokia" in call for call in console_calls))

    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch.object(RevokeVPNCertificateCommand, "_check_ssm_connectivity")
    @patch.object(RevokeVPNCertificateCommand, "_check_certificate_exists")
    @patch.object(RevokeVPNCertificateCommand, "_revoke_certificate")
    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_revoke_failure(
        self,
        mock_console_error,
        mock_revoke,
        mock_check_cert,
        mock_check_ssm,
        mock_discover,
    ):
        """Test run with revocation failure."""
        mock_discover.return_value = {
            "instance_id": "i-1234567890abcdef0",
            "name": "test-vpn-server",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }
        mock_check_ssm.return_value = True
        mock_check_cert.return_value = True
        mock_revoke.side_effect = Exception("Revocation failed")

        args = Mock()
        args.partner_name = "partner-nokia"

        with self.assertRaises(Exception) as context:
            self.command.run(args)

        self.assertIn("Revocation failed", str(context.exception))
        mock_console_error.assert_called()

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    def test_revoke_certificate(self, mock_run_ssm):
        """Test revoke certificate method."""
        mock_run_ssm.return_value = {"Status": "Success"}

        self.command._revoke_certificate("i-1234567890abcdef0", "partner-nokia")

        # Verify correct command was sent
        call_args = mock_run_ssm.call_args[0]
        self.assertIn("EASYRSA_BATCH=1 ./easyrsa revoke partner-nokia", call_args[1])

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    def test_update_crl(self, mock_run_ssm):
        """Test update CRL method."""
        mock_run_ssm.return_value = {"Status": "Success"}

        self.command._update_crl("i-1234567890abcdef0")

        # Verify correct commands were sent
        call_args = mock_run_ssm.call_args[0]
        self.assertIn("EASYRSA_BATCH=1 ./easyrsa gen-crl", call_args[1])
        self.assertIn("cp pki/crl.pem /etc/openvpn/", call_args[1])
        self.assertIn("chmod 644 /etc/openvpn/crl.pem", call_args[1])

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    def test_remove_ccd_config_success(self, mock_run_ssm):
        """Test successful remove CCD config."""
        mock_run_ssm.return_value = {"Status": "Success"}

        self.command._remove_ccd_config("i-1234567890abcdef0", "partner-nokia")

        # Verify correct commands were sent
        call_args = mock_run_ssm.call_args[0]
        self.assertIn("rm -f /etc/openvpn/ccd/partner-nokia", call_args[1])
        self.assertIn("rm -f /etc/openvpn/ccd/partner-nokia", call_args[1].lower())

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    @patch("telco_cli.utils.logging.console.print")
    def test_remove_ccd_config_with_warning(self, mock_console_print, mock_run_ssm):
        """Test remove CCD config with warning on failure."""
        mock_run_ssm.side_effect = Exception("Command failed")

        # Should not raise exception, just print warning
        self.command._remove_ccd_config("i-1234567890abcdef0", "partner-nokia")

        # Verify warning was printed
        console_calls = [str(call) for call in mock_console_print.call_args_list]
        self.assertTrue(
            any("Warning: Could not remove CCD config" in call for call in console_calls)
        )

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    def test_cleanup_certificate_files_success(self, mock_run_ssm):
        """Test successful cleanup certificate files."""
        mock_run_ssm.return_value = {"Status": "Success"}

        self.command._cleanup_certificate_files("i-1234567890abcdef0", "partner-nokia")

        # Verify correct commands were sent
        call_args = mock_run_ssm.call_args[0]
        self.assertIn("rm -f /etc/openvpn/partner-nokia.ovpn", call_args[1])

    @patch.object(RevokeVPNCertificateCommand, "_run_ssm_command")
    @patch("telco_cli.utils.logging.console.print")
    def test_cleanup_certificate_files_with_warning(self, mock_console_print, mock_run_ssm):
        """Test cleanup certificate files with warning on failure."""
        mock_run_ssm.side_effect = Exception("Command failed")

        # Should not raise exception, just print warning
        self.command._cleanup_certificate_files("i-1234567890abcdef0", "partner-nokia")

        # Verify warning was printed
        console_calls = [str(call) for call in mock_console_print.call_args_list]
        self.assertTrue(
            any("Warning: Could not clean up certificate files" in call for call in console_calls)
        )

    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch("telco_cli.utils.logging.console_error.print")
    def test_run_generic_exception(self, mock_console_error, mock_discover):
        """Test run with generic exception."""
        mock_discover.side_effect = Exception("Generic error")

        args = Mock()
        args.partner_name = "partner-nokia"

        with self.assertRaises(Exception) as context:
            self.command.run(args)

        self.assertIn("Generic error", str(context.exception))
        mock_console_error.assert_called()

    def test_valid_partner_names(self):
        """Test various valid partner name formats."""
        valid_names = [
            "partner-nokia",
            "partner_verizon",
            "partner123",
            "PARTNER-NOKIA",
            "partner_nokia_123",
            "partner-nokia-test",
        ]

        for name in valid_names:
            args = Mock()
            args.partner_name = name
            # Should not raise ValueError for name validation
            # We'll mock the server discovery to make it fail at that step
            with patch.object(self.command, "_discover_openvpn_server", return_value=None):
                try:
                    self.command.run(args)
                except ValueError:
                    self.fail(f"Valid partner name '{name}' was rejected")
                except Exception:
                    # Other exceptions are expected (e.g., no server found)
                    pass

    @patch("builtins.input", return_value="no")
    @patch("telco_cli.utils.prompts.console")
    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.console")
    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch.object(RevokeVPNCertificateCommand, "_check_certificate_exists")
    @patch.object(RevokeVPNCertificateCommand, "_check_ssm_connectivity", return_value=True)
    def test_user_cancellation(
        self,
        mock_ssm_check,
        mock_check_cert,
        mock_discover,
        mock_console,
        mock_prompts_console,
        mock_input,
    ):
        """Test user cancellation during confirmation prompt (lines 86-87)."""
        # Setup mocks
        mock_discover.return_value = {"name": "test-server", "instance_id": "i-123456789"}
        mock_check_cert.return_value = True  # Certificate exists

        args = Mock()
        args.partner_name = "test-partner"
        args.yes = False  # Don't skip confirmation

        # Should return early when user cancels
        self.command.run(args)

        # Verify input was called and console showed cancellation message
        mock_input.assert_called_once()
        mock_prompts_console.print.assert_any_call("[yellow]Operation cancelled.[/yellow]")

    @patch("builtins.input", return_value="yes")
    @patch("telco_cli.commands.vpn.revoke_vpn_certificate.console")
    @patch.object(RevokeVPNCertificateCommand, "_discover_openvpn_server")
    @patch.object(RevokeVPNCertificateCommand, "_check_certificate_exists")
    @patch.object(RevokeVPNCertificateCommand, "_check_ssm_connectivity", return_value=True)
    @patch("telco_cli.utils.logging.console_error.print")
    def test_certificate_deleted_during_confirmation(
        self,
        mock_console_error,
        mock_ssm_check,
        mock_check_cert,
        mock_discover,
        mock_console,
        mock_input,
    ):
        """Test race condition: certificate deleted after initial check but before revocation.

        This tests the TOCTOU (Time-of-Check Time-of-Use) race condition fix where:
        Certificate exists during initial check
        User confirms the operation
        Certificate is re-checked after confirmation (the fix)
        Certificate was deleted by another user during confirmation
        Command should detect this and abort gracefully
        """
        mock_discover.return_value = {
            "name": "test-vpn-server",
            "instance_id": "i-1234567890abcdef0",
            "endpoint": "54.123.45.67",
            "port": 1194,
            "network": "10.10.10.0/24",
        }

        # Certificate exists initially, then deleted during confirmation
        mock_check_cert.side_effect = [True, False]

        args = Mock()
        args.partner_name = "partner-nokia"
        args.yes = False

        self.command.run(args)

        # Verify certificate was checked twice (initial + re-check)
        self.assertEqual(
            mock_check_cert.call_count,
            2,
            "Certificate should be checked twice: initial check + re-check after confirmation",
        )

        # Verify error message shown when certificate not found on re-check
        console_error_calls = [str(call) for call in mock_console_error.call_args_list]
        self.assertTrue(
            any(
                "Certificate for partner 'partner-nokia' no longer exists" in call
                for call in console_error_calls
            ),
            "Should display error when certificate is deleted during confirmation",
        )


if __name__ == "__main__":
    unittest.main()
