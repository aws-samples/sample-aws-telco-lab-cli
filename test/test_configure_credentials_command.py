"""Tests for Configure Credentials Command."""

import argparse
from unittest.mock import patch

from telco_cli.commands.configure_credentials import ConfigureCredentialsCommand


class TestConfigureCredentialsCommand:
    """Test cases for ConfigureCredentialsCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = ConfigureCredentialsCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "configure-credentials"

    def test_description_property(self):
        """Test command description property."""
        assert "Configure AWS account to profile mappings" in self.command.description

    def test_register_arguments(self):
        """Test argument registration."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)
        # Check that subparsers are created
        assert hasattr(parser, "_subparsers")

    def test_run_add_mapping(self):
        """Test adding credential mapping."""
        args = argparse.Namespace()
        args.action = "add"
        args.account_id = "123456789012"
        args.profiles = "profile1,profile2"

        with patch.object(self.command, "_add_mapping") as mock_add:
            self.command.run(args)
            mock_add.assert_called_once_with("123456789012", "profile1,profile2")

    def test_run_list_mappings(self):
        """Test listing credential mappings."""
        args = argparse.Namespace()
        args.action = "list"

        with patch.object(self.command, "_list_mappings") as mock_list:
            self.command.run(args)
            mock_list.assert_called_once()

    def test_run_remove_mapping(self):
        """Test removing credential mapping."""
        args = argparse.Namespace()
        args.action = "remove"
        args.account_id = "123456789012"

        with patch.object(self.command, "_remove_mapping") as mock_remove:
            self.command.run(args)
            mock_remove.assert_called_once_with("123456789012")
