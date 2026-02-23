"""Tests for Delete Partner Command."""

import argparse
from unittest.mock import Mock, patch

import pytest

from telco_cli.commands.delete_partner import DeletePartnerCommand


class TestDeletePartnerCommand:
    """Test cases for DeletePartnerCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = DeletePartnerCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "delete-partner"

    def test_description_property(self):
        """Test command description property."""
        assert "Delete a partner account" in self.command.description

    def test_register_arguments(self):
        """Test argument registration."""
        parser = Mock()
        self.command.register(parser)
        parser.add_argument.assert_called()

    def test_register_arguments_with_force(self):
        """Test argument registration includes force flag."""
        parser = Mock()
        self.command.register(parser)
        calls = parser.add_argument.call_args_list
        force_call = any("--force" in str(call) for call in calls)
        assert force_call

    @patch("telco_cli.commands.delete_partner.boto3.client")
    def test_run_success(self, mock_boto3):
        """Test successful partner deletion."""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        args = argparse.Namespace(
            partner_name="test-partner", force=True, account_id="123456789012"
        )

        with patch.object(self.command, "_delete_partner_real") as mock_delete:
            mock_delete.return_value = {"Success": True}
            self.command.run(args)
            mock_delete.assert_called_once_with(args)

    @patch("telco_cli.commands.delete_partner.boto3.client")
    def test_run_with_confirmation(self, mock_boto3):
        """Test partner deletion with confirmation."""
        mock_client = Mock()
        mock_boto3.return_value = mock_client

        args = argparse.Namespace(partner_name="test-partner", force=False, account_id=None)

        with patch("builtins.input", return_value="yes"):
            with patch.object(self.command, "_delete_partner_real") as mock_delete:
                mock_delete.return_value = {"Success": True}
                self.command.run(args)
                mock_delete.assert_called_once_with(args)

    @patch("telco_cli.commands.delete_partner.boto3.client")
    def test_partner_not_found_with_similar_names(self, mock_boto3):
        """Test partner not found with similar name suggestions (lines 109-110)."""
        from telco_cli.exceptions.base_exception import TelcoCLIException
        from telco_cli.exceptions.error_codes import ErrorCode

        mock_client = Mock()
        mock_boto3.return_value = mock_client

        mock_client.list_accounts.return_value = {
            "Accounts": [
                {"Name": "test-partner-prod", "Id": "123456789012", "Status": "ACTIVE"},
                {"Name": "test-partner-dev", "Id": "123456789013", "Status": "ACTIVE"},
                {"Name": "other-account", "Id": "123456789014", "Status": "ACTIVE"},
            ]
        }

        # Use a name that shares words with the accounts (word-based matching)
        args = argparse.Namespace(partner_name="test-partner-staging", force=True, account_id=None)

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._delete_partner_real(args)

        e = exc_info.value
        assert e.error_code == ErrorCode.VALIDATION_ERROR
        # Should find similar names because they share "test" and "partner" words
        error_str = str(e)
        assert "Did you mean one of these:" in error_str
        assert "test-partner-prod" in error_str or "test-partner-dev" in error_str

    @patch("telco_cli.commands.delete_partner.boto3.client")
    def test_partner_not_found_no_similar_names(self, mock_boto3):
        """Test partner not found without similar names (lines 109-110)."""
        from telco_cli.exceptions.base_exception import TelcoCLIException
        from telco_cli.exceptions.error_codes import ErrorCode

        mock_client = Mock()
        mock_boto3.return_value = mock_client

        mock_client.list_accounts.return_value = {
            "Accounts": [
                {"Name": "completely-different-account", "Id": "123456789012", "Status": "ACTIVE"},
                {"Name": "another-unrelated-account", "Id": "123456789013", "Status": "ACTIVE"},
            ]
        }

        # Use a name with no common words
        args = argparse.Namespace(partner_name="xyz-unique-name", force=True, account_id=None)

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._delete_partner_real(args)

        e = exc_info.value
        assert e.error_code == ErrorCode.VALIDATION_ERROR
        error_str = str(e)
        assert "Available accounts: 2 total" in error_str
        assert "Did you mean" not in error_str

    def test_telco_cli_exception_preservation(self):
        """Test that TelcoCLIException is re-raised as-is (lines 66, 68)."""
        from telco_cli.exceptions.base_exception import TelcoCLIException
        from telco_cli.exceptions.error_codes import ErrorCode

        args = argparse.Namespace(partner_name="test-partner", force=True)

        # Mock _delete_partner_real to raise TelcoCLIException
        with patch.object(self.command, "_delete_partner_real") as mock_delete:
            original_exception = TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Original error")
            mock_delete.side_effect = original_exception

            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            e = exc_info.value
            # Should be the same exception object (preserved)
            assert e is original_exception
            assert e.error_code == ErrorCode.VALIDATION_ERROR
            assert "Original error" in str(e)

    def test_generic_exception_wrapping(self):
        """Test that generic exceptions are wrapped (line 72)."""
        from telco_cli.exceptions.base_exception import TelcoCLIException
        from telco_cli.exceptions.error_codes import ErrorCode

        args = argparse.Namespace(partner_name="test-partner", force=True)

        with patch.object(self.command, "_delete_partner_real") as mock_delete:
            mock_delete.side_effect = Exception("Generic error")

            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            e = exc_info.value
            assert e.error_code == ErrorCode.PARTNER_LISTING_FAILED
            assert "Generic error" in str(e)
