# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""List Partners Command implementation."""

import argparse
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.services.account_provisioning import AccountProvisioningEngine
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger

logger = get_logger(__name__)


class ListPartnersCommand(BaseCommand):
    """List all partner accounts."""

    def __init__(self):
        self.console = Console()

    @property
    def name(self) -> str:
        return "list-partners"

    @property
    def description(self) -> str:
        return "List all partner accounts"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--status",
            choices=["Active", "Inactive", "All"],
            default="All",
            help="Filter partners by status",
        )
        parser.add_argument(
            "--output",
            choices=["json", "table"],
            default="table",
            help="Output format (default: table)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the list partners command."""
        try:
            logger.info(f"Listing partners with status filter: {args.status}")

            provisioning_engine = AccountProvisioningEngine()
            partners = provisioning_engine.list_partner_accounts()

            # Apply null check for partner names (Day 2 fix)
            for partner in partners:
                partner_name = partner.get("Name")
                if partner_name:
                    partner["Name"] = partner_name.upper()

            # Filter by status if specified
            if args.status != "All":
                partners = [p for p in partners if p.get("Status") == args.status]

            # Display results
            if hasattr(args, "output") and args.output == "table":
                self._display_partners_table(partners)
            else:
                self._display_partners_json(partners)

        except TelcoCLIException:
            raise
        except KeyError as e:
            logger.error(f"Missing required field in partner data: {e}")
            raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, f"Missing required field: {e}")
        except Exception as e:
            logger.exception("Failed to list partners")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, str(e))

    def _display_partners_table(self, partners: List[Dict[str, Any]]) -> None:
        """Display partners in a rich table format."""
        if not partners:
            self.console.print("📭 [yellow]No partners found.[/yellow]")
            return

        self.console.print(f"\n🤝 [bold cyan]Found {len(partners)} partner(s):[/bold cyan]")

        # Create table
        table = Table(title="Partner Accounts")
        table.add_column("Partner Name", style="cyan", no_wrap=True)
        table.add_column("Account ID", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("Created", style="green")

        for partner in partners:
            # Use safe dictionary access (Day 2 fix)
            partner_name = partner.get("Name", "Unknown")
            if partner_name:
                partner_name = partner_name.upper()

            status = partner.get("Status", "Unknown")
            # Color-code status
            if status == "ACTIVE":
                status_display = f"[green]{status}[/green]"
            elif status == "SUSPENDED":
                status_display = f"[red]{status}[/red]"
            else:
                status_display = f"[yellow]{status}[/yellow]"

            table.add_row(
                partner_name,
                partner.get("AccountId", "Unknown"),
                status_display,
                partner.get("CreatedAt", "Unknown"),
            )

        self.console.print(table)

    def _display_partners_json(self, partners: List[Dict[str, Any]]) -> None:
        """Display partners in JSON format (legacy)."""
        if not partners:
            console.print("📭 [yellow]No partners found.[/yellow]")
            return

        console.print(f"\n🤝 [bold cyan]Found {len(partners)} partner(s):[/bold cyan]")

        for partner in partners:
            # Use safe dictionary access (Day 2 fix)
            partner_name = partner.get("Name", "Unknown")
            if partner_name:
                partner_name = partner_name.upper()

            status = partner.get("Status", "Unknown")
            # Color-code status
            if status == "ACTIVE":
                status_display = f"[green]{status}[/green]"
            elif status == "SUSPENDED":
                status_display = f"[red]{status}[/red]"
            else:
                status_display = f"[yellow]{status}[/yellow]"

            console.print(f"├── 🏢 Partner: [bold cyan]{partner_name}[/bold cyan]")
            console.print(
                f"│   ├── 🆔 Account ID: [yellow]{partner.get('AccountId', 'Unknown')}[/yellow]"
            )
            console.print(f"│   ├── 📊 Status: {status_display}")
            console.print(f"│   └── 📅 Created: [blue]{partner.get('CreatedAt', 'Unknown')}[/blue]")
