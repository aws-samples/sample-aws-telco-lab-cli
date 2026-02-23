"""Tests for Update Credentials Command."""

import argparse
from pathlib import Path
from unittest.mock import patch

from telco_cli.commands.update_credentials import UpdateCredentialsCommand


class TestUpdateCredentialsCommand:
    """Test cases for UpdateCredentialsCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = UpdateCredentialsCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "update-credentials"

    def test_description_property(self):
        """Test command description property."""
        assert "Update AWS credentials" in self.command.description

    def test_register_arguments(self):
        """Test argument registration."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)
        # Check that required arguments are registered
        assert any(action.dest == "account_id" for action in parser._actions)

    def test_register_arguments_with_format(self):
        """Test argument registration includes format option."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)
        # Check that format argument is registered
        assert any(action.dest == "format" for action in parser._actions)

    @patch("telco_cli.commands.update_credentials.Path.home")
    @patch("builtins.input")
    def test_run_interactive_mode(self, mock_input, mock_home):
        """Test interactive credential update."""
        mock_home.return_value = Path("/tmp")
        mock_input.side_effect = [
            "export AWS_ACCESS_KEY_ID=ASIATEST123456789",
            "export AWS_SECRET_ACCESS_KEY=secretTEST123456789",
            "export AWS_SESSION_TOKEN=tokenTEST123456789",
            "",  # End input
        ]

        args = argparse.Namespace(account_id="123456789012", format="interactive")

        with patch.object(self.command, "_load_account_mappings") as mock_load:
            mock_load.return_value = {"123456789012": ["profile1", "profile2"]}
            with patch.object(self.command, "_get_interactive_credentials") as mock_get:
                mock_get.return_value = {
                    "access_key": "ASIATEST123456789",
                    "secret_key": "secretTEST123456789",
                    "session_token": "tokenTEST123456789",
                }
                with patch.object(self.command, "_update_aws_credentials"):
                    self.command.run(args)

    @patch("sys.stdin.read")
    def test_run_stdin_mode(self, mock_stdin):
        """Test stdin credential update."""
        mock_stdin.return_value = """
        export AWS_ACCESS_KEY_ID=ASIATEST123456789
        export AWS_SECRET_ACCESS_KEY=secretTEST123456789
        export AWS_SESSION_TOKEN=tokenTEST123456789
        """

        args = argparse.Namespace(account_id="123456789012", format="stdin")

        with patch.object(self.command, "_load_account_mappings") as mock_load:
            mock_load.return_value = {"123456789012": ["profile1", "profile2"]}
            with patch.object(self.command, "_get_stdin_credentials") as mock_get:
                mock_get.return_value = {
                    "access_key": "ASIATEST123456789",
                    "secret_key": "secretTEST123456789",
                    "session_token": "tokenTEST123456789",
                }
                with patch.object(self.command, "_update_aws_credentials"):
                    self.command.run(args)

    def test_parse_credentials_bash_format(self):
        """Test parsing bash export format."""
        cred_text = """
        export AWS_ACCESS_KEY_ID=ASIATEST123456789
        export AWS_SECRET_ACCESS_KEY=secretTEST123456789
        export AWS_SESSION_TOKEN=tokenTEST123456789
        """

        result = self.command._parse_credentials(cred_text)

        assert result["access_key"] == "ASIATEST123456789"
        assert result["secret_key"] == "secretTEST123456789"
        assert result["session_token"] == "tokenTEST123456789"

    def test_parse_credentials_windows_format(self):
        """Test parsing Windows SET format."""
        cred_text = """
        set AWS_ACCESS_KEY_ID=ASIATEST123456789
        set AWS_SECRET_ACCESS_KEY=secretTEST123456789
        set AWS_SESSION_TOKEN=tokenTEST123456789
        """

        result = self.command._parse_credentials(cred_text)

        assert result["access_key"] == "ASIATEST123456789"
        assert result["secret_key"] == "secretTEST123456789"
        assert result["session_token"] == "tokenTEST123456789"
