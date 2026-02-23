"""Tests for Health Command."""

import argparse
from unittest.mock import Mock, patch

import pytest

from telco_cli.commands.health_check import HealthCommand


class TestHealthCommand:
    """Test cases for HealthCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = HealthCommand()

    def test_name_property(self):
        """Test command name."""
        assert self.command.name == "health"

    def test_description_property(self):
        """Test command description."""
        assert "Run health checks" in self.command.description

    def test_register_arguments(self):
        """Test argument registration."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        args = parser.parse_args(["--format", "text"])
        assert args.format == "text"

    def test_run_json_format(self):
        """Test health command with JSON format."""
        self.command._run_all_checks = Mock(
            return_value={
                "overall_status": "healthy",
                "aws_connectivity": {"status": "healthy"},
                "organizations_access": {"status": "healthy"},
            }
        )

        args = Mock()
        args.format = "json"

        with patch("telco_cli.utils.logging.console.print") as mock_print:
            self.command.run(args)
            mock_print.assert_called()

    def test_run_text_format(self):
        """Test health command with text format."""
        self.command._run_all_checks = Mock(
            return_value={
                "overall_status": "healthy",
                "timestamp": "2023-01-01T00:00:00Z",
                "aws_connectivity": {"status": "healthy", "response_time_ms": 100},
                "organizations_access": {"status": "healthy", "response_time_ms": 200},
            }
        )

        args = Mock()
        args.format = "text"

        with patch("telco_cli.utils.logging.console.print") as mock_print:
            self.command.run(args)
            mock_print.assert_called()

    def test_run_unhealthy_status(self):
        """Test health command with unhealthy status."""
        self.command._run_all_checks = Mock(
            return_value={
                "overall_status": "unhealthy",
                "aws_connectivity": {"status": "unhealthy", "error": "Connection failed"},
            }
        )

        args = Mock()
        args.format = "json"

        with pytest.raises(SystemExit) as exc_info:
            with patch("telco_cli.utils.logging.console.print"):
                self.command.run(args)

        assert exc_info.value.code == 1

    def test_run_with_exception(self):
        """Test health command when exception occurs."""
        # Mock _run_all_checks to raise an exception
        self.command._run_all_checks = Mock(side_effect=Exception("Test exception"))

        args = Mock()
        args.format = "json"

        # Mock the formatter and its methods
        mock_formatter = Mock()
        mock_formatter.get_exit_code.return_value = 1

        with patch("telco_cli.commands.health_check.get_formatter", return_value=mock_formatter):
            with pytest.raises(SystemExit) as exc_info:
                self.command.run(args)

            # Verify the formatter methods were called
            mock_formatter.format_error.assert_called_once()
            mock_formatter.get_exit_code.assert_called_once()

            # Verify exit code
            assert exc_info.value.code == 1

    def test_run_all_checks_returns_healthy_status(self):
        """Test _run_all_checks method returns expected structure."""
        result = self.command._run_all_checks()

        # Verify the structure of the returned data
        assert "overall_status" in result
        assert "timestamp" in result
        assert "aws_connectivity" in result

        # Verify the values
        assert result["overall_status"] == "healthy"
        assert result["aws_connectivity"]["status"] == "healthy"
        assert result["aws_connectivity"]["response_time_ms"] == 50

        # Verify timestamp is a valid ISO format string
        from datetime import datetime

        datetime.fromisoformat(result["timestamp"])  # Should not raise exception

    @patch("telco_cli.commands.health_check.logger")
    def test_logging_during_execution(self, mock_logger):
        """Test that appropriate logging occurs during command execution."""
        self.command._run_all_checks = Mock(
            return_value={
                "overall_status": "healthy",
                "aws_connectivity": {"status": "healthy"},
            }
        )

        args = Mock()
        args.format = "json"

        with patch("telco_cli.utils.logging.console.print"):
            self.command.run(args)

        # Verify logging calls
        mock_logger.info.assert_any_call("Starting health check with format: json")
        mock_logger.info.assert_any_call("Health check completed with status: healthy")

    @patch("telco_cli.commands.health_check.logger")
    def test_logging_during_unhealthy_execution(self, mock_logger):
        """Test logging during unhealthy status execution."""
        self.command._run_all_checks = Mock(
            return_value={
                "overall_status": "unhealthy",
                "aws_connectivity": {"status": "unhealthy"},
            }
        )

        args = Mock()
        args.format = "json"

        with pytest.raises(SystemExit):
            with patch("telco_cli.utils.logging.console.print"):
                self.command.run(args)

        # Verify warning log for unhealthy status
        mock_logger.warning.assert_called_with("Health check failed - exiting with error code")

    @patch("telco_cli.commands.health_check.logger")
    def test_logging_during_exception(self, mock_logger):
        """Test logging when exception occurs."""
        test_exception = Exception("Test exception")
        self.command._run_all_checks = Mock(side_effect=test_exception)

        args = Mock()
        args.format = "json"

        mock_formatter = Mock()
        mock_formatter.get_exit_code.return_value = 1

        with patch("telco_cli.commands.health_check.get_formatter", return_value=mock_formatter):
            with pytest.raises(SystemExit):
                self.command.run(args)

        # Verify error logging
        mock_logger.error.assert_called_with(
            f"Health check failed with exception: {test_exception}"
        )
