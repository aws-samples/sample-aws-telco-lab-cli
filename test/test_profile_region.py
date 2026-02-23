"""Tests for profile and region environment variable functionality."""

import os
from unittest.mock import Mock, patch

from telco_cli.cli import main


class TestProfileRegionSupport:
    """Test cases for --profile and --region CLI arguments."""

    @patch.dict(os.environ, {}, clear=True)
    def test_profile_sets_environment_variable(self):
        """Test that --profile sets AWS_PROFILE environment variable."""
        mock_command = Mock()
        mock_command.name = "test-command"
        mock_command.description = "Test command"
        mock_command.register = Mock()
        mock_command.run = Mock()

        mock_args = Mock()
        mock_args.command = "test-command"
        mock_args._run = mock_command.run
        mock_args.verbose = False
        mock_args.quiet = False
        mock_args.log_file = None
        mock_args.profile = "test-profile"
        mock_args.region = None

        with (
            patch("telco_cli.cli.discover_commands", return_value=[mock_command]),
            patch("argparse.ArgumentParser.parse_args", return_value=mock_args),
            patch("telco_cli.cli.setup_logging"),
        ):
            main()

            assert os.environ.get("AWS_PROFILE") == "test-profile"
            mock_command.run.assert_called_once_with(mock_args)

    @patch.dict(os.environ, {}, clear=True)
    def test_region_sets_environment_variable(self):
        """Test that --region sets AWS_DEFAULT_REGION environment variable."""
        mock_command = Mock()
        mock_command.name = "test-command"
        mock_command.description = "Test command"
        mock_command.register = Mock()
        mock_command.run = Mock()

        mock_args = Mock()
        mock_args.command = "test-command"
        mock_args._run = mock_command.run
        mock_args.verbose = False
        mock_args.quiet = False
        mock_args.log_file = None
        mock_args.profile = None
        mock_args.region = "us-west-2"

        with (
            patch("telco_cli.cli.discover_commands", return_value=[mock_command]),
            patch("argparse.ArgumentParser.parse_args", return_value=mock_args),
            patch("telco_cli.cli.setup_logging"),
        ):
            main()

            assert os.environ.get("AWS_DEFAULT_REGION") == "us-west-2"
            mock_command.run.assert_called_once_with(mock_args)

    @patch.dict(os.environ, {}, clear=True)
    def test_both_profile_and_region_set_environment_variables(self):
        """Test that both --profile and --region set their respective environment variables."""
        mock_command = Mock()
        mock_command.name = "test-command"
        mock_command.description = "Test command"
        mock_command.register = Mock()
        mock_command.run = Mock()

        mock_args = Mock()
        mock_args.command = "test-command"
        mock_args._run = mock_command.run
        mock_args.verbose = False
        mock_args.quiet = False
        mock_args.log_file = None
        mock_args.profile = "prod-profile"
        mock_args.region = "eu-central-1"

        with (
            patch("telco_cli.cli.discover_commands", return_value=[mock_command]),
            patch("argparse.ArgumentParser.parse_args", return_value=mock_args),
            patch("telco_cli.cli.setup_logging"),
        ):
            main()

            assert os.environ.get("AWS_PROFILE") == "prod-profile"
            assert os.environ.get("AWS_DEFAULT_REGION") == "eu-central-1"
            mock_command.run.assert_called_once_with(mock_args)

    @patch.dict(os.environ, {}, clear=True)
    def test_none_values_do_not_set_environment_variables(self):
        """Test that None values for profile/region don't set environment variables."""
        mock_command = Mock()
        mock_command.name = "test-command"
        mock_command.description = "Test command"
        mock_command.register = Mock()
        mock_command.run = Mock()

        mock_args = Mock()
        mock_args.command = "test-command"
        mock_args._run = mock_command.run
        mock_args.verbose = False
        mock_args.quiet = False
        mock_args.log_file = None
        mock_args.profile = None
        mock_args.region = None

        with (
            patch("telco_cli.cli.discover_commands", return_value=[mock_command]),
            patch("argparse.ArgumentParser.parse_args", return_value=mock_args),
            patch("telco_cli.cli.setup_logging"),
        ):
            main()

            assert "AWS_PROFILE" not in os.environ
            assert "AWS_DEFAULT_REGION" not in os.environ
            mock_command.run.assert_called_once_with(mock_args)
