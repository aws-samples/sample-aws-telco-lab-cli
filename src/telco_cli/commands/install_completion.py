# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Install shell completion command."""

import argparse
import os

from telco_cli.types.base_command import BaseCommand
from telco_cli.utils.logging import console


class InstallCompletionCommand(BaseCommand):
    """Install shell completion for bash/zsh."""

    @property
    def name(self) -> str:
        return "install-completion"

    @property
    def description(self) -> str:
        return "Install shell completion for bash/zsh"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--shell",
            choices=["bash", "zsh"],
            default=self._detect_shell(),
            help="Shell to install completion for (default: auto-detect)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the install-completion command."""
        shell = args.shell

        console.print(f"[cyan]Installing completion for {shell}...[/cyan]\n")

        if shell == "bash":
            self._install_bash()
        elif shell == "zsh":
            self._install_zsh()

    def _detect_shell(self) -> str:
        """Detect current shell."""
        shell = os.getenv("SHELL", "")
        if "zsh" in shell:
            return "zsh"
        return "bash"

    def _install_bash(self) -> None:
        """Install bash completion."""
        console.print("[green]Bash completion setup:[/green]\n")
        console.print("Add the following to your ~/.bashrc:\n")
        console.print('[yellow]eval "$(register-python-argcomplete telcocli)"[/yellow]\n')
        console.print("Then run: [cyan]source ~/.bashrc[/cyan]")

    def _install_zsh(self) -> None:
        """Install zsh completion."""
        console.print("[green]Zsh completion setup:[/green]\n")
        console.print("Add the following to your ~/.zshrc:\n")
        console.print("[yellow]autoload -U bashcompinit[/yellow]")
        console.print("[yellow]bashcompinit[/yellow]")
        console.print('[yellow]eval "$(register-python-argcomplete telcocli)"[/yellow]\n')
        console.print("Then run: [cyan]source ~/.zshrc[/cyan]")
