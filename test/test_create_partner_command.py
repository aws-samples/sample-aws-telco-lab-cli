"""Tests for CreatePartnerCommand."""

from unittest.mock import Mock, patch

import pytest

from telco_cli.commands.create_partner import CreatePartnerCommand
from telco_cli.exceptions import ErrorCode, TelcoCLIException


class TestCreatePartnerCommand:
    """Test cases for CreatePartnerCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = CreatePartnerCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "create-partner"

    def test_description_property(self):
        """Test command description property."""
        expected = "Create partner account with cross-account assume role configuration"
        assert self.command.description == expected

    def test_parse_duration_to_days_valid(self):
        """Test duration parsing with valid inputs."""
        assert self.command._parse_duration_to_days("30d") == 30
        assert self.command._parse_duration_to_days("48h") == 2
        assert self.command._parse_duration_to_days("1440m") == 1
        assert self.command._parse_duration_to_days("7") == 7

    def test_parse_duration_to_days_invalid(self):
        """Test duration parsing with invalid inputs."""
        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._parse_duration_to_days("invalid")
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    @patch("telco_cli.commands.create_partner.validate_partner_name")
    def test_run_invalid_partner_name(self, mock_validate):
        """Test run with invalid partner name."""
        mock_validate.return_value = False

        args = Mock()
        args.partner_name = "invalid-name!"
        args.partner_account_id = "123456789012"

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.run(args)
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR

    @patch("telco_cli.commands.create_partner.validate_aws_account_id")
    @patch("telco_cli.commands.create_partner.validate_partner_name")
    def test_run_invalid_account_id(self, mock_validate_name, mock_validate_id):
        """Test run with invalid account ID."""
        mock_validate_name.return_value = True
        mock_validate_id.return_value = False

        args = Mock()
        args.partner_name = "test-partner"
        args.partner_account_id = "invalid"

        with pytest.raises(TelcoCLIException) as exc_info:
            self.command.run(args)
        assert exc_info.value.error_code == ErrorCode.VALIDATION_ERROR
