"""Tests for List Partners Command."""

import argparse
from unittest.mock import Mock, patch

import pytest

from telco_cli.commands.list_partners import ListPartnersCommand
from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode


class TestListPartnersCommand:
    """Test cases for ListPartnersCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = ListPartnersCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "list-partners"

    def test_description_property(self):
        """Test command description property."""
        assert "List all partner accounts" in self.command.description

    def test_register_arguments(self):
        """Test argument registration."""
        parser = Mock()
        self.command.register(parser)
        parser.add_argument.assert_called()

    def test_register_arguments_default(self):
        """Test argument registration with default status."""
        parser = Mock()
        self.command.register(parser)
        calls = parser.add_argument.call_args_list
        status_call = any("--status" in str(call) for call in calls)
        assert status_call

    @patch("telco_cli.commands.list_partners.AccountProvisioningEngine")
    def test_run_success(self, mock_engine_class):
        """Test successful partner listing."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        mock_partners = [
            {"Name": "partner1", "AccountId": "123456789012", "Status": "Active"},
            {"Name": "partner2", "AccountId": "123456789013", "Status": "Inactive"},
        ]
        mock_engine.list_partner_accounts.return_value = mock_partners

        args = argparse.Namespace(status="All", output="table")

        self.command.run(args)
        mock_engine.list_partner_accounts.assert_called_once()

    @patch("telco_cli.commands.list_partners.AccountProvisioningEngine")
    def test_run_with_status_filter(self, mock_engine_class):
        """Test partner listing with status filter."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.list_partner_accounts.return_value = []

        args = argparse.Namespace(status="Active", output="table")

        self.command.run(args)

    @patch("telco_cli.commands.list_partners.AccountProvisioningEngine")
    def test_run_empty_results(self, mock_engine_class):
        """Test partner listing with no results."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.list_partner_accounts.return_value = []

        args = argparse.Namespace(status="All", output="table")

        self.command.run(args)

    @patch("telco_cli.commands.list_partners.AccountProvisioningEngine")
    def test_telcocli_exception_reraised(self, mock_engine_class):
        """Test that TelcoCLIException is re-raised as-is."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        original_exception = TelcoCLIException(ErrorCode.AWS_API_ERROR, "AWS error")
        mock_engine.list_partner_accounts.side_effect = original_exception

        args = argparse.Namespace(status="All", output="table")

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.run(args)

        assert exc_info.value is original_exception
        assert exc_info.value.error_code == ErrorCode.AWS_API_ERROR
