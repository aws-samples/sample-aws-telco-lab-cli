"""Tests for Describe Partner Command."""

import argparse
from unittest.mock import Mock, patch

import pytest

from telco_cli.commands.describe_partner import DescribePartnerCommand
from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode


class TestDescribePartnerCommand:
    """Test cases for DescribePartnerCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = DescribePartnerCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "describe-partner"

    def test_description_property(self):
        """Test command description property."""
        assert "Describe a specific partner account" in self.command.description

    def test_register_arguments(self):
        """Test argument registration."""
        parser = Mock()
        self.command.register(parser)
        parser.add_argument.assert_called_with(
            "--partner-name", required=True, help="Name of the partner to describe"
        )

    @patch("telco_cli.commands.describe_partner.AccountProvisioningEngine")
    def test_run_success(self, mock_engine_class):
        """Test successful partner description."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        mock_partner_data = {
            "partner_name": "test-partner",
            "account_id": "123456789012",
            "status": "Active",
            "created_date": "2023-01-01",
        }
        mock_engine.get_partner_account.return_value = mock_partner_data

        args = argparse.Namespace(partner_name="test-partner")

        self.command.run(args)
        mock_engine.get_partner_account.assert_called_once_with("test-partner")

    @patch("telco_cli.commands.describe_partner.AccountProvisioningEngine")
    def test_run_partner_not_found(self, mock_engine_class):
        """Test partner not found scenario."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_partner_account.return_value = None

        args = argparse.Namespace(partner_name="nonexistent-partner")

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.run(args)

        assert "Partner 'nonexistent-partner' not found" in str(exc_info.value)

    @patch("telco_cli.commands.describe_partner.AccountProvisioningEngine")
    def test_telcocli_exception_reraised(self, mock_engine_class):
        """Test that TelcoCLIException is re-raised as-is."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        original_exception = TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Original error")
        mock_engine.get_partner_account.side_effect = original_exception

        args = argparse.Namespace(partner_name="test-partner")

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.run(args)

        assert exc_info.value is original_exception
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    @patch("telco_cli.commands.describe_partner.AccountProvisioningEngine")
    def test_value_error_handling(self, mock_engine_class):
        """Test ValueError handling."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.get_partner_account.side_effect = ValueError("Invalid value")

        args = argparse.Namespace(partner_name="test-partner")

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.run(args)

        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
        assert "Invalid value" in str(exc_info.value)
