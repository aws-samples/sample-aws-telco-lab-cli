"""Tests for install_completion command."""

import argparse
import os
from unittest.mock import patch

from telco_cli.commands.install_completion import InstallCompletionCommand


class TestInstallCompletionCommand:
    """Test cases for InstallCompletionCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = InstallCompletionCommand()

    def test_name_property(self):
        """Test command name property."""
        assert self.command.name == "install-completion"

    def test_description_property(self):
        """Test command description property."""
        assert "Install shell completion" in self.command.description

    def test_register(self):
        """Test argument registration."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # Check that shell argument is registered
        args = parser.parse_args(["--shell", "bash"])
        assert args.shell == "bash"

    @patch.dict(os.environ, {"SHELL": "/bin/bash"})
    def test_detect_shell_bash(self):
        """Test shell detection for bash."""
        result = self.command._detect_shell()
        assert result == "bash"

    @patch.dict(os.environ, {"SHELL": "/usr/bin/zsh"})
    def test_detect_shell_zsh(self):
        """Test shell detection for zsh."""
        result = self.command._detect_shell()
        assert result == "zsh"

    @patch.dict(os.environ, {"SHELL": ""})
    def test_detect_shell_default(self):
        """Test shell detection default."""
        result = self.command._detect_shell()
        assert result == "bash"

    @patch("telco_cli.commands.install_completion.console")
    def test_install_bash(self, mock_console):
        """Test bash installation instructions."""
        self.command._install_bash()

        # Verify console.print was called with bash instructions
        assert mock_console.print.called
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        bash_instruction = 'eval "$(register-python-argcomplete telcocli)"'
        assert any(bash_instruction in call for call in calls)

    @patch("telco_cli.commands.install_completion.console")
    def test_install_zsh(self, mock_console):
        """Test zsh installation instructions."""
        self.command._install_zsh()

        # Verify console.print was called with zsh instructions
        assert mock_console.print.called
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        zsh_instruction = 'eval "$(register-python-argcomplete telcocli)"'
        assert any(zsh_instruction in call for call in calls)

    @patch("telco_cli.commands.install_completion.console")
    def test_run_bash(self, mock_console):
        """Test running command for bash."""
        args = argparse.Namespace(shell="bash")
        self.command.run(args)

        # Verify console.print was called
        assert mock_console.print.called

    @patch("telco_cli.commands.install_completion.console")
    def test_run_zsh(self, mock_console):
        """Test running command for zsh."""
        args = argparse.Namespace(shell="zsh")
        self.command.run(args)

        # Verify console.print was called
        assert mock_console.print.called
