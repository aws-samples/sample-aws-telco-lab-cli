# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Help command implementation."""

import argparse

from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console


class HelpCommand(BaseCommand):
    """Display help information for AWS CLI commands."""

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "Display help information for AWS CLI commands"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "command_parts",
            nargs="*",
            help="AWS command parts to get help for (e.g., 'ec2 describe-instances')",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the help command."""
        # Build command as a list to avoid shell injection vulnerabilities
        aws_command_list = ["aws"] + list(args.command_parts) + ["help"]
        aws_command_str = " ".join(aws_command_list)

        console.print(f"[cyan]Executing:[/cyan] {aws_command_str}\n")
        self._execute(aws_command_list)
