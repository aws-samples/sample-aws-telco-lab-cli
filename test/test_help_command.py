"""Tests for HelpCommand."""

import argparse
from unittest.mock import patch

import pytest

from telco_cli.commands.help import HelpCommand
from telco_cli.exceptions import ErrorCode, TelcoCLIException


class TestHelpCommand:
    """Test cases for HelpCommand."""

    @pytest.fixture
    def help_command(self):
        """Provide a HelpCommand instance."""
        return HelpCommand()

    def test_command_properties(self, help_command):
        """Test command name and description."""
        assert help_command.name == "help"
        assert "help information" in help_command.description.lower()

    @pytest.mark.parametrize(
        "input_args, expected_parts",
        [
            ([], []),
            (["ec2", "describe-instances"], ["ec2", "describe-instances"]),
            (["s3", "ls"], ["s3", "ls"]),
            (["cloudformation"], ["cloudformation"]),
        ],
    )
    def test_register_parser(self, help_command, input_args, expected_parts):
        """Test argument parser registration with different inputs."""
        parser = argparse.ArgumentParser()
        help_command.register(parser)

        args = parser.parse_args(input_args)
        assert args.command_parts == expected_parts

    @pytest.mark.parametrize(
        "command_parts, expected_command, expected_output",
        [
            ([], ["aws", "help"], "Executing: aws help"),
            (["ec2"], ["aws", "ec2", "help"], "Executing: aws ec2 help"),
            (
                ["ec2", "describe-instances"],
                ["aws", "ec2", "describe-instances", "help"],
                "Executing: aws ec2 describe-instances help",
            ),
            (["s3", "ls"], ["aws", "s3", "ls", "help"], "Executing: aws s3 ls help"),
        ],
    )
    def test_successful_execution(
        self, help_command, command_parts, expected_command, expected_output, capfd
    ):
        """Test successful command execution and console output."""
        args = argparse.Namespace(command_parts=command_parts)

        # Mock _execute to avoid actual subprocess call
        with patch.object(help_command, "_execute") as mock_execute:
            help_command.run(args)

            # Verify _execute was called with correct command
            mock_execute.assert_called_once_with(expected_command)

            # Verify console output (strip ANSI codes)
            captured = capfd.readouterr()
            import re

            clean_output = re.sub(r"\x1b\[[0-9;]*m", "", captured.out)
            assert expected_output in clean_output

    @pytest.mark.parametrize(
        "exception, error_code",
        [
            (
                TelcoCLIException(ErrorCode.COMMAND_EXECUTION_ERROR, "Command failed"),
                ErrorCode.COMMAND_EXECUTION_ERROR,
            ),
            (
                TelcoCLIException(ErrorCode.AWS_CONNECTION_ERROR, "AWS connection failed"),
                ErrorCode.AWS_CONNECTION_ERROR,
            ),
            (
                TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Invalid input"),
                ErrorCode.VALIDATION_ERROR,
            ),
        ],
    )
    def test_error_propagation(self, help_command, exception, error_code):
        """Test that exceptions from _execute are properly propagated."""
        args = argparse.Namespace(command_parts=[])

        with patch.object(help_command, "_execute", side_effect=exception):
            with pytest.raises(TelcoCLIException) as exc_info:
                help_command.run(args)

            assert exc_info.value.error_code == error_code
            assert exc_info.value is exception

    def test_command_list_construction(self, help_command):
        """Test that AWS command list is constructed correctly."""
        test_cases = [
            ([], ["aws", "help"]),
            (["ec2"], ["aws", "ec2", "help"]),
            (["s3", "cp", "file.txt"], ["aws", "s3", "cp", "file.txt", "help"]),
        ]

        for command_parts, expected_list in test_cases:
            args = argparse.Namespace(command_parts=command_parts)

            with patch.object(help_command, "_execute") as mock_execute:
                help_command.run(args)
                mock_execute.assert_called_once_with(expected_list)
