"""Tests for TelcoCLIException base exception class."""

import logging
from unittest.mock import patch

import pytest

from telco_cli.exceptions import ErrorCode, TelcoCLIException


class TestTelcoCLIException:
    """Test cases for TelcoCLIException base class."""

    @pytest.mark.parametrize(
        "error_code, message_template, params, expected_substring",
        [
            # Basic initialization without parameters
            (ErrorCode.VALIDATION_ERROR, "Simple error message", (), "Simple error message"),
            # Message with single parameter
            (
                ErrorCode.INVALID_PARTNER_NAME,
                "Invalid partner name: '{}' is not allowed",
                ("test-partner",),
                "Invalid partner name: 'test-partner' is not allowed",
            ),
            # Message with multiple parameters
            (
                ErrorCode.AWS_CONNECTION_ERROR,
                "Failed to connect to AWS {} in region {}",
                ("EC2", "us-east-1"),
                "Failed to connect to AWS EC2 in region us-east-1",
            ),
            # Message without parameters
            (
                ErrorCode.CERTIFICATE_NOT_FOUND,
                "Certificate not found in the system",
                (),
                "Certificate not found in the system",
            ),
            # Real-world scenarios
            (
                ErrorCode.INVALID_DURATION,
                "Duration {} is invalid",
                ("5 minutes",),
                "Duration 5 minutes is invalid",
            ),
            (
                ErrorCode.AWS_CREDENTIALS_MISSING,
                "AWS credentials missing for profile: {}",
                ("default",),
                "AWS credentials missing for profile: default",
            ),
            (
                ErrorCode.SSM_AGENT_OFFLINE,
                "SSM agent offline on instance {}",
                ("i-1234567890abcdef0",),
                "SSM agent offline on instance i-1234567890abcdef0",
            ),
        ],
    )
    def test_message_formatting_scenarios(
        self, error_code, message_template, params, expected_substring
    ):
        """Test various message formatting scenarios."""
        exception = TelcoCLIException(error_code, message_template, *params)

        assert exception.error_code == error_code
        assert expected_substring in str(exception)
        assert exception.exit_code == int(error_code)

    def test_message_formatting_failure_handling(self):
        """Test graceful handling of message formatting failures."""
        error_code = ErrorCode.FILE_WRITE_ERROR
        bad_template = "Missing placeholder {} and {}"
        single_param = "only-one"

        # Should not raise an exception, but log the error
        with patch.object(
            logging.getLogger("telco_cli.exceptions.base_exception"), "exception"
        ) as mock_logger:
            exception = TelcoCLIException(error_code, bad_template, single_param)

            mock_logger.assert_called_once()
            args = mock_logger.call_args[0]
            assert "Failed to format exception message" in args[0]
            assert bad_template in args[1]
            assert single_param in str(args[2])

            # Original message should be preserved
            assert bad_template in str(exception)

    @pytest.mark.parametrize(
        "error_code, custom_exit, expected_exit",
        [
            # Default exit codes from error codes
            (ErrorCode.SUCCESS, None, 0),
            (ErrorCode.VALIDATION_ERROR, None, 2),
            (ErrorCode.AWS_CONNECTION_ERROR, None, 3),
            (ErrorCode.SERVER_DISCOVERY_ERROR, None, 4),
            (ErrorCode.SSM_CONNECTION_ERROR, None, 5),
            (ErrorCode.COMMAND_EXECUTION_ERROR, None, 6),
            (ErrorCode.FILE_OPERATION_ERROR, None, 7),
            (ErrorCode.CERTIFICATE_ERROR, None, 8),
            (ErrorCode.CONFIGURATION_ERROR, None, 9),
            # Custom exit code override
            (ErrorCode.VALIDATION_ERROR, 99, 99),
            # Explicit None uses error code value
            (ErrorCode.CERTIFICATE_ERROR, None, 8),
        ],
    )
    def test_exit_code_logic(self, error_code, custom_exit, expected_exit):
        """Test exit code assignment logic."""
        if custom_exit == 99:  # Custom override case
            exception = TelcoCLIException(error_code, "Test message", exit_code=custom_exit)
        else:
            exception = TelcoCLIException(error_code, "Test message")

        assert exception.exit_code == expected_exit
        assert exception.error_code == error_code

    def test_string_representation_format(self):
        """Test the custom string representation format."""
        error_code = ErrorCode.INVALID_SUBNET
        message = "Invalid subnet format"

        exception = TelcoCLIException(error_code, message)

        string_repr = str(exception)
        expected_format = f"[{error_code.name} - {error_code.value}] {message}"
        assert string_repr == expected_format

    def test_exception_behavior(self):
        """Test exception inheritance and raising/catching behavior."""
        error_code = ErrorCode.NO_VPN_SERVER_FOUND
        message = "No VPN server found"

        # Test inheritance
        exception = TelcoCLIException(error_code, message)
        assert isinstance(exception, Exception)
        assert isinstance(exception, TelcoCLIException)

        with pytest.raises(TelcoCLIException) as exc_info:
            raise exception

        caught_exception = exc_info.value
        assert caught_exception is exception
        assert caught_exception.error_code == error_code
        assert message in str(caught_exception)

    def test_exception_attributes_accessible(self):
        """Test that all exception attributes are accessible."""
        error_code = ErrorCode.ROUTING_CONFIG_ERROR
        message = "Routing configuration error"
        custom_exit = 42

        exception = TelcoCLIException(error_code, message, exit_code=custom_exit)

        assert exception.error_code == error_code
        assert exception.exit_code == custom_exit
        assert hasattr(exception, "args")  # From base Exception class
