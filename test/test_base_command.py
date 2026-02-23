"""Tests for BaseCommand abstract base class."""

import argparse
import subprocess
from abc import ABC
from unittest.mock import patch

import pytest

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.types.base_command import BaseCommand


class ConcreteCommand(BaseCommand):
    """Concrete implementation for testing."""

    def __init__(self, name="test", description="Test command"):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def register(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--test", help="Test argument")

    def run(self, args: argparse.Namespace) -> None:
        if hasattr(args, "should_fail"):
            raise TelcoCLIException(ErrorCode.UNKNOWN_ERROR, "Test error")


class TestBaseCommand:
    """Test cases for BaseCommand abstract base class."""

    @pytest.fixture
    def concrete_command(self):
        """Provide a concrete implementation of BaseCommand for testing."""
        return ConcreteCommand()

    def test_abstract_base_class_and_concrete_implementation(self):
        """Test abstract base class enforcement and concrete implementation."""
        # Cannot instantiate abstract class directly
        with pytest.raises(TypeError) as exc_info:
            BaseCommand()
        assert "Can't instantiate abstract class" in str(exc_info.value)

        command = ConcreteCommand()
        assert command.name == "test"
        assert command.description == "Test command"
        assert isinstance(command, BaseCommand)
        assert isinstance(command, ABC)

        # Custom properties
        custom_command = ConcreteCommand(name="custom", description="Custom description")
        assert custom_command.name == "custom"
        assert custom_command.description == "Custom description"

    def test_abstract_methods_implementation(self, concrete_command):
        """Test that concrete class implements all abstract methods."""
        # Test register method
        parser = argparse.ArgumentParser()
        concrete_command.register(parser)
        args = parser.parse_args(["--test", "value"])
        assert args.test == "value"

        # Test run method - success case
        args = argparse.Namespace(test="value")
        concrete_command.run(args)  # Should not raise

        # Test run method - failure case
        args = argparse.Namespace(should_fail=True)
        with pytest.raises(TelcoCLIException) as exc_info:
            concrete_command.run(args)
        assert exc_info.value.error_code == ErrorCode.UNKNOWN_ERROR

    @pytest.mark.parametrize(
        "side_effect, expected_error_code, expected_message_part, console_error_message",
        [
            # CalledProcessError
            (
                subprocess.CalledProcessError(1, "test_command"),
                ErrorCode.COMMAND_EXECUTION_ERROR,
                "Command failed",
                "❌ Error executing system command",
            ),
            # FileNotFoundError
            (
                FileNotFoundError("command not found"),
                ErrorCode.COMMAND_EXECUTION_ERROR,
                "CLI tool not found",
                "❌ CLI tool not found",
            ),
            # TimeoutExpired
            (
                subprocess.TimeoutExpired("test_command", 300),
                ErrorCode.COMMAND_EXECUTION_ERROR,
                "Command timed out",
                "❌ Command timed out after 5 minutes",
            ),
            # Unexpected exception
            (
                RuntimeError("Unexpected error"),
                ErrorCode.UNKNOWN_ERROR,
                "Unexpected error",
                None,  # No console error for unexpected exceptions
            ),
        ],
    )
    @patch("subprocess.run")
    @patch("telco_cli.types.base_command.console_error")
    @patch("telco_cli.types.base_command.logger")
    def test_execute_error_handling(
        self,
        mock_logger,
        mock_console_error,
        mock_run,
        concrete_command,
        side_effect,
        expected_error_code,
        expected_message_part,
        console_error_message,
    ):
        """Test _execute method error handling for various exceptions."""
        mock_run.side_effect = side_effect

        with pytest.raises(TelcoCLIException) as exc_info:
            concrete_command._execute(["test_command"])

        assert exc_info.value.error_code == expected_error_code
        assert expected_message_part in str(exc_info.value)

        if console_error_message:
            mock_console_error.print.assert_called_once_with(console_error_message, style="error")

        if isinstance(side_effect, RuntimeError):
            mock_logger.exception.assert_called_once_with("Unexpected error in command execution")

    @patch("subprocess.run")
    def test_execute_telco_cli_exception_passthrough(self, mock_run, concrete_command):
        """Test that TelcoCLIException is not double-wrapped."""
        original_exception = TelcoCLIException(ErrorCode.AWS_CONNECTION_ERROR, "AWS error")
        mock_run.side_effect = original_exception

        with pytest.raises(TelcoCLIException) as exc_info:
            concrete_command._execute(["test_command"])

        assert exc_info.value is original_exception
        assert exc_info.value.error_code == ErrorCode.AWS_CONNECTION_ERROR

    @patch("subprocess.run")
    @patch("telco_cli.types.base_command.logger")
    def test_execute_success_and_logging(self, mock_logger, mock_run, concrete_command):
        """Test successful command execution and logging."""
        command = ["aws", "s3", "ls"]
        concrete_command._execute(command)

        mock_run.assert_called_once_with(command, shell=False, check=True, timeout=300)
        mock_logger.debug.assert_called_once_with("Executing command: %s", "aws s3 ls")

    def test_abstract_methods_enforcement(self):
        """Test that all abstract methods must be implemented."""
        # Test various incomplete implementations
        incomplete_classes = [
            # Missing all abstract methods
            type("IncompleteCommand1", (BaseCommand,), {}),
            # Missing some abstract methods
            type(
                "IncompleteCommand2", (BaseCommand,), {"name": property(lambda self: "incomplete")}
            ),
            # Missing register method
            type(
                "IncompleteCommand3",
                (BaseCommand,),
                {
                    "name": property(lambda self: "incomplete"),
                    "description": property(lambda self: "Incomplete command"),
                    "run": lambda self, args: None,
                },
            ),
        ]

        for incomplete_class in incomplete_classes:
            with pytest.raises(TypeError):
                incomplete_class()

    def test_multiple_concrete_implementations(self):
        """Test that multiple concrete implementations can coexist."""

        class AnotherCommand(BaseCommand):
            @property
            def name(self) -> str:
                return "another"

            @property
            def description(self) -> str:
                return "Another command"

            def register(self, parser: argparse.ArgumentParser) -> None:
                parser.add_argument("--another", help="Another argument")

            def run(self, args: argparse.Namespace) -> None:
                pass

        command1 = ConcreteCommand()
        command2 = AnotherCommand()

        assert command1.name == "test"
        assert command2.name == "another"
        assert isinstance(command1, BaseCommand)
        assert isinstance(command2, BaseCommand)
