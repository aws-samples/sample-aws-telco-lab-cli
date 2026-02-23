"""Tests for output formatters."""

import json
from unittest.mock import patch

from botocore.exceptions import ClientError, NoCredentialsError

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.utils.constants import OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TEXT
from telco_cli.utils.formatters import (
    AccountsOutputFormatter,
    HealthCheckOutputFormatter,
    OutputFormatter,
    get_formatter,
)


class TestOutputFormatter:
    """Test cases for OutputFormatter base class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = OutputFormatter()

    def test_extract_error_data_from_dict(self):
        """Test extracting error data from dictionary."""
        error_dict = {"Error": {"Code": "TestError", "Message": "Test message"}}
        result = self.formatter._extract_error_data(error_dict)
        assert result == error_dict

    def test_extract_error_data_from_telco_cli_exception(self):
        """Test extracting error data from TelcoCLIException."""
        exception = TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Test validation error")
        result = self.formatter._extract_error_data(exception)

        expected = {
            "Error": {
                "Code": "VALIDATION_ERROR",
                "Message": "[VALIDATION_ERROR - 2] Test validation error",
                "ExitCode": 2,
            }
        }
        assert result == expected

    def test_extract_error_data_from_no_credentials_error(self):
        """Test extracting error data from NoCredentialsError."""
        exception = NoCredentialsError()
        result = self.formatter._extract_error_data(exception)

        expected = {
            "Error": {
                "Code": "NoCredentialsError",
                "Message": "AWS credentials not configured",
                "ExitCode": 3,
            }
        }
        assert result == expected

    def test_extract_error_data_from_client_error(self):
        """Test extracting error data from ClientError."""
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied to resource"}}
        exception = ClientError(error_response, "TestOperation")
        result = self.formatter._extract_error_data(exception)

        expected = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "AWS service error: Access denied to resource",
                "ExitCode": 3,
            }
        }
        assert result == expected

    def test_extract_error_data_from_generic_exception(self):
        """Test extracting error data from generic exception."""
        exception = ValueError("Generic error message")
        result = self.formatter._extract_error_data(exception)

        expected = {
            "Error": {
                "Code": "UnexpectedError",
                "Message": "Generic error message",
                "ExitCode": 1,
            }
        }
        assert result == expected

    def test_get_exit_code_from_telco_cli_exception(self):
        """Test getting exit code from TelcoCLIException."""
        exception = TelcoCLIException(ErrorCode.AWS_CONNECTION_ERROR, "Test error")
        exit_code = self.formatter.get_exit_code(exception)
        assert exit_code == 3

    def test_get_exit_code_from_no_credentials_error(self):
        """Test getting exit code from NoCredentialsError."""
        exception = NoCredentialsError()
        exit_code = self.formatter.get_exit_code(exception)
        assert exit_code == 3

    def test_get_exit_code_from_generic_exception(self):
        """Test getting exit code from generic exception."""
        exception = ValueError("Test error")
        exit_code = self.formatter.get_exit_code(exception)
        assert exit_code == 1

    def test_get_exit_code_from_dict(self):
        """Test getting exit code from dictionary error."""
        error_dict = {"Error": {"Code": "TestError", "Message": "Test message", "ExitCode": 5}}
        exit_code = self.formatter.get_exit_code(error_dict)
        assert exit_code == 5

    def test_get_exit_code_from_dict_no_exit_code(self):
        """Test getting exit code from dictionary without ExitCode."""
        error_dict = {"Error": {"Code": "TestError", "Message": "Test message"}}
        exit_code = self.formatter.get_exit_code(error_dict)
        assert exit_code == ErrorCode.UNKNOWN_ERROR.value

    @patch("telco_cli.utils.formatters.console_error.print")
    def test_format_error(self, mock_print):
        """Test formatting error output."""
        exception = TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Test error")
        self.formatter.format_error(exception)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        error_data = json.loads(call_args)
        assert error_data["Error"]["Code"] == "VALIDATION_ERROR"

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_json(self, mock_print):
        """Test formatting success output in JSON format."""
        data = {"status": "success", "message": "Test message"}
        self.formatter.format_success(data, OUTPUT_FORMAT_JSON)

        mock_print.assert_called_once_with(json.dumps(data, indent=2))


class TestHealthCheckOutputFormatter:
    """Test cases for HealthCheckOutputFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = HealthCheckOutputFormatter()

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_json(self, mock_print):
        """Test formatting health check success in JSON format."""
        data = {
            "overall_status": "healthy",
            "timestamp": "2023-01-01T00:00:00Z",
            "aws_connectivity": {"status": "healthy", "response_time_ms": 100},
        }
        self.formatter.format_success(data, OUTPUT_FORMAT_JSON)

        mock_print.assert_called_once_with(json.dumps(data, indent=2))

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_text(self, mock_print):
        """Test formatting health check success in text format."""
        data = {
            "overall_status": "healthy",
            "timestamp": "2023-01-01T00:00:00Z",
            "aws_connectivity": {"status": "healthy", "response_time_ms": 100},
        }
        self.formatter.format_success(data, OUTPUT_FORMAT_TEXT)

        # Should call print multiple times for text format
        assert mock_print.call_count > 1

        # Check that status and timestamp are printed
        calls = []
        for call in mock_print.call_args_list:
            if call[0]:  # Check if there are positional arguments
                calls.append(call[0][0])

        status_printed = any("Overall Status: HEALTHY" in str(call) for call in calls)
        timestamp_printed = any("Timestamp: 2023-01-01T00:00:00Z" in str(call) for call in calls)

        assert status_printed
        assert timestamp_printed

    @patch("telco_cli.utils.formatters.console.print")
    def test_print_text_format_with_error_in_check(self, mock_print):
        """Test _print_text_format with error in health check result."""
        results = {
            "overall_status": "unhealthy",
            "timestamp": "2023-01-01T00:00:00Z",
            "aws_connectivity": {
                "status": "unhealthy",
                "error": "Connection timeout",
                "message": "Failed to connect to AWS",
            },
        }

        self.formatter._print_text_format(results)

        # Should print error and message
        calls = [str(call) for call in mock_print.call_args_list]
        error_printed = any("Error: Connection timeout" in call for call in calls)
        message_printed = any("Message: Failed to connect to AWS" in call for call in calls)

        assert error_printed
        assert message_printed

    @patch("telco_cli.utils.formatters.console.print")
    def test_print_text_format_with_response_time(self, mock_print):
        """Test _print_text_format with response time in health check result."""
        results = {
            "overall_status": "healthy",
            "timestamp": "2023-01-01T00:00:00Z",
            "database_check": {"status": "healthy", "response_time_ms": 250},
        }

        self.formatter._print_text_format(results)

        # Should print response time
        calls = [str(call) for call in mock_print.call_args_list]
        response_time_printed = any("Response Time: 250ms" in call for call in calls)

        assert response_time_printed

    @patch("telco_cli.utils.formatters.console_error.print")
    def test_format_error_health_specific(self, mock_print):
        """Test formatting health check error with health-specific context."""
        exception = TelcoCLIException(ErrorCode.AWS_CONNECTION_ERROR, "AWS connection failed")
        self.formatter.format_error(exception)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        error_data = json.loads(call_args)

        assert error_data["overall_status"] == "unhealthy"
        assert "AWS connection failed" in error_data["error"]
        assert error_data["error_code"] == "AWS_CONNECTION_ERROR"


class TestAccountsOutputFormatter:
    """Test cases for AccountsOutputFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = AccountsOutputFormatter()

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_json(self, mock_print):
        """Test formatting accounts success in JSON format."""
        data = {
            "Success": True,
            "Accounts": [
                {"AccountId": "123456789012", "AccountName": "Test Account", "Status": "ACTIVE"}
            ],
            "TotalCount": 1,
        }
        self.formatter.format_success(data, OUTPUT_FORMAT_JSON)

        mock_print.assert_called_once_with(json.dumps(data, indent=2))

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_table_format(self, mock_print):
        """Test formatting accounts success in table format."""
        data = {
            "Success": True,
            "Accounts": [
                {
                    "AccountId": "123456789012",
                    "AccountName": "Test Account",
                    "Status": "ACTIVE",
                    "AccountType": "partner",
                }
            ],
            "Summary": {
                "TotalAccounts": 1,
                "ByStatus": {"ACTIVE": 1},
                "ByType": {"partner": 1},
                "ActiveByType": {"partner": 1},
            },
        }
        self.formatter.format_success(data, "table")

        # Should print table header, separator, account row, and summary
        assert mock_print.call_count >= 4

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_table_no_accounts(self, mock_print):
        """Test formatting table with no accounts."""
        data = {"Success": True, "Accounts": [], "Summary": {"TotalAccounts": 0}}
        self.formatter.format_success(data, "table")

        # Should print "📭 No accounts found." with style
        mock_print.assert_called_with("📭 No accounts found.", style="yellow")

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_summary_format(self, mock_print):
        """Test formatting accounts success in summary format."""
        data = {
            "Success": True,
            "Accounts": [
                {
                    "AccountId": "123456789012",
                    "AccountName": "Test Account",
                    "Status": "ACTIVE",
                    "AccountType": "partner",
                }
            ],
            "Summary": {
                "TotalAccounts": 1,
                "ByStatus": {"ACTIVE": 1},
                "ByType": {"partner": 1},
                "ActiveByType": {"partner": 1},
                "OrganizationalUnits": ["Production", "Development", "Test"],
            },
        }
        self.formatter.format_success(data, "summary")

        # Should print summary header and details
        assert mock_print.call_count >= 5

        # Check that summary content is printed
        calls = [str(call) for call in mock_print.call_args_list]
        summary_printed = any("AWS Organizations / Control Tower Summary" in call for call in calls)
        total_printed = any("Total Accounts:" in call and "1" in call for call in calls)

        assert summary_printed
        assert total_printed

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_summary_format_with_many_ous(self, mock_print):
        """Test formatting summary with many organizational units."""
        # Create more than MAX_OU_DISPLAY_COUNT OUs
        many_ous = [f"OU-{i}" for i in range(15)]  # More than MAX_OU_DISPLAY_COUNT (10)

        data = {
            "Success": True,
            "Accounts": [],
            "Summary": {
                "TotalAccounts": 0,
                "ByStatus": {},
                "ByType": {},
                "ActiveByType": {},
                "OrganizationalUnits": many_ous,
            },
        }
        self.formatter.format_success(data, "summary")

        # Check that "... and X more" message is printed
        calls = [str(call) for call in mock_print.call_args_list]
        more_message_printed = any("... and" in call and "5 more" in call for call in calls)
        assert more_message_printed

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_table_format_error_case(self, mock_print):
        """Test formatting table when Success is False."""
        data = {
            "Success": False,
            "Error": {"Code": "TestError", "Message": "Test error message"},
        }

        self.formatter.format_success(data, "table")

        # Should print error message directly
        mock_print.assert_called_with("❌ Error: Failed to retrieve accounts", style="bold red")

    @patch("telco_cli.utils.formatters.console.print")
    def test_format_success_summary_format_error_case(self, mock_print):
        """Test formatting summary when Success is False."""
        data = {
            "Success": False,
            "Error": {"Code": "TestError", "Message": "Test error message"},
        }

        self.formatter.format_success(data, "summary")

        # Should print error message directly
        mock_print.assert_called_with("❌ Error: Failed to retrieve accounts", style="bold red")


class TestGetFormatter:
    """Test cases for get_formatter function."""

    def test_get_health_formatter(self):
        """Test getting health formatter."""
        formatter = get_formatter("health")
        assert isinstance(formatter, HealthCheckOutputFormatter)

    def test_get_accounts_formatter(self):
        """Test getting accounts formatter."""
        formatter = get_formatter("accounts")
        assert isinstance(formatter, AccountsOutputFormatter)

    def test_get_default_formatter(self):
        """Test getting default formatter for unknown type."""
        formatter = get_formatter("unknown")
        assert isinstance(formatter, OutputFormatter)
        assert not isinstance(formatter, (HealthCheckOutputFormatter, AccountsOutputFormatter))
