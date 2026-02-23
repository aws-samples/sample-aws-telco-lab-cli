# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""List All Accounts Command implementation with comprehensive AWS Organizations view."""

import argparse
import logging
import sys
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

try:
    from typing import Counter as CounterType
except ImportError:
    from typing_extensions import Counter as CounterType

import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console
from telco_cli.utils.account_constants import (
    ACCOUNT_STATUSES,
    ACCOUNT_TYPES,
    OU_PREFIX,
    ROOT_OU_NAME,
    UNKNOWN_OU,
)
from telco_cli.utils.account_type_detector import AccountTypeDetector
from telco_cli.utils.constants import (
    AWS_ERROR_ACCESS_DENIED,
    AWS_ERROR_ORGANIZATIONS_NOT_IN_USE,
    OUTPUT_FORMATS,
)
from telco_cli.utils.formatters import get_formatter

logger = logging.getLogger(__name__)


class ListAllAccountsCommand(BaseCommand):
    """List all accounts in AWS Organizations with comprehensive Control Tower view."""

    def __init__(self):
        self.console = Console()

    @property
    def name(self) -> str:
        return "list-all-accounts"

    @property
    def description(self) -> str:
        return "List all accounts in AWS Organizations with comprehensive Control Tower view"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--status",
            choices=ACCOUNT_STATUSES,
            help="Filter by AWS account status",
        )
        parser.add_argument(
            "--account-type",
            choices=ACCOUNT_TYPES + ["all"],
            default="all",
            help="Filter by account type (default: all)",
        )
        parser.add_argument(
            "--include-ou",
            action="store_true",
            help="Include Organizational Unit information for each account",
        )
        parser.add_argument(
            "--output",
            choices=OUTPUT_FORMATS + ["table"],
            default="table",
            help="Output format (default: table)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the list all accounts command."""
        logger.info(
            f"Starting list-all-accounts command with filters: status={args.status}, type={args.account_type}, output={args.output}"
        )
        formatter = get_formatter("accounts")

        try:
            result = self._list_all_accounts_detailed(args)
            logger.info(f"Successfully retrieved {result.get('TotalCount', 0)} accounts")

            if args.output == "table":
                self._display_accounts_table(result)
            else:
                formatter.format_success(result, args.output)

        except TelcoCLIException:
            raise
        except Exception as e:
            logger.error(f"Failed to list accounts: {e}")
            if args.output == "table":
                console.print(f"❌ [red]Failed to list accounts: {str(e)}[/red]")
                sys.exit(1)
            else:
                formatter.format_error(e)
                sys.exit(formatter.get_exit_code(e))

    def _display_accounts_table(self, result: Dict[str, Any]) -> None:
        """Display accounts in rich table format."""
        accounts = result.get("Accounts", [])

        if not accounts:
            self.console.print("📭 [yellow]No accounts found[/yellow]")
            return

        # Summary
        self.console.print(
            f"\n🏢 [bold cyan]AWS Organizations Accounts ({len(accounts)} total):[/bold cyan]"
        )

        # Statistics
        stats = result.get("Statistics", {})
        if stats:
            self.console.print("\n📊 [bold]Account Statistics:[/bold]")
            for key, value in stats.items():
                if isinstance(value, dict):
                    self.console.print(f"├── {key}:")
                    for sub_key, sub_value in value.items():
                        self.console.print(f"│   ├── {sub_key}: [cyan]{sub_value}[/cyan]")
                else:
                    self.console.print(f"├── {key}: [cyan]{value}[/cyan]")

        # Accounts table
        table = Table(title="AWS Accounts")
        table.add_column("Account ID", style="yellow", no_wrap=True)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="blue")
        table.add_column("Type", style="magenta")
        table.add_column("OU", style="green")
        table.add_column("Email", style="dim")

        for account in accounts:
            # Color-code status
            status = account.get("Status", "Unknown")
            if status == "ACTIVE":
                status_display = f"[green]{status}[/green]"
            elif status == "SUSPENDED":
                status_display = f"[red]{status}[/red]"
            else:
                status_display = f"[yellow]{status}[/yellow]"

            table.add_row(
                account.get("AccountId", "Unknown"),
                account.get("AccountName", "Unknown"),
                status_display,
                account.get("AccountType", "Unknown"),
                account.get("OrganizationalUnit", "Unknown"),
                account.get("Email", "Unknown"),
            )

        self.console.print(table)
        self.console.print(f"\n📈 [bold green]Total: {len(accounts)} accounts[/bold green]")

    def _list_all_accounts_detailed(self, args: argparse.Namespace) -> Dict[str, Any]:
        """List all accounts from AWS Organizations with comprehensive details."""
        try:
            org_client = boto3.client("organizations")

            paginator = org_client.get_paginator("list_accounts")
            all_accounts = []

            for page in paginator.paginate():
                for account in page["Accounts"]:
                    try:
                        tags_response = org_client.list_tags_for_resource(ResourceId=account["Id"])
                        tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("Tags", [])}
                    except ClientError:
                        tags = {}

                    # Get OU information if requested
                    ou_info = None
                    if args.include_ou:
                        ou_info = self._get_ou_information(org_client, account["Id"])

                    account_type = AccountTypeDetector.determine_account_type(account, tags)

                    # Apply filters
                    if args.status and account["Status"] != args.status:
                        continue

                    if args.account_type != "all" and account_type != args.account_type:
                        continue

                    account_info = {
                        "AccountId": account["Id"],
                        "AccountName": account["Name"],
                        "Email": account["Email"],
                        "Status": account["Status"],
                        "AccountType": account_type,
                        "JoinedMethod": account["JoinedMethod"],
                        "JoinedTimestamp": (
                            account["JoinedTimestamp"].isoformat()
                            if account.get("JoinedTimestamp")
                            else None
                        ),
                        "Tags": tags,
                    }

                    if ou_info:
                        account_info["OrganizationalUnit"] = ou_info

                    all_accounts.append(account_info)

            # Sort accounts by type, then by name
            all_accounts.sort(key=lambda x: (x["AccountType"], x["AccountName"]))

            summary = self._generate_summary(all_accounts)

            result = {
                "Success": True,
                "Accounts": all_accounts,
                "TotalCount": len(all_accounts),
                "LastUpdated": datetime.now().isoformat(),
                "Summary": summary,
                "FilteredBy": {
                    "Status": args.status if args.status else "All",
                    "AccountType": args.account_type,
                },
            }

            return result

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == AWS_ERROR_ORGANIZATIONS_NOT_IN_USE:
                raise TelcoCLIException(
                    ErrorCode.ORGANIZATIONS_NOT_ENABLED,
                    "AWS Organizations is not enabled in this account",
                )
            elif error_code == AWS_ERROR_ACCESS_DENIED:
                raise TelcoCLIException(
                    ErrorCode.ORGANIZATIONS_ACCESS_DENIED,
                    "Access denied. Ensure you have organizations:ListAccounts permissions",
                )
            else:
                # Re-raise the ClientError to be handled by unified error handling
                raise

    def _get_ou_information(self, org_client, account_id: str) -> Dict[str, Any]:
        """Get Organizational Unit information for an account."""
        try:
            parents = org_client.list_parents(ChildId=account_id)
            if parents["Parents"]:
                parent_id = parents["Parents"][0]["Id"]
                if parent_id.startswith(OU_PREFIX):
                    # Get OU details
                    ou_details = org_client.describe_organizational_unit(
                        OrganizationalUnitId=parent_id
                    )
                    return {"Id": parent_id, "Name": ou_details["OrganizationalUnit"]["Name"]}
                else:
                    return {"Id": parent_id, "Name": ROOT_OU_NAME}
        except ClientError as e:
            # Log the error but don't raise - return unknown OU instead
            # This prevents OU lookup failures from breaking the entire account listing
            logger.warning(f"Failed to get OU information for account {account_id}: {e}")

        return UNKNOWN_OU

    def _generate_summary(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for all accounts."""
        account_counts_by_status: CounterType[str] = Counter()
        account_counts_by_type: CounterType[str] = Counter()
        active_account_counts_by_type: CounterType[str] = Counter()
        organizational_unit_names = set()

        for account in accounts:
            account_counts_by_status[account["Status"]] += 1
            account_counts_by_type[account["AccountType"]] += 1

            if account["Status"] == "ACTIVE":
                active_account_counts_by_type[account["AccountType"]] += 1

            if "OrganizationalUnit" in account:
                organizational_unit_names.add(account["OrganizationalUnit"]["Name"])

        summary = {
            "TotalAccounts": len(accounts),
            "ByStatus": dict(account_counts_by_status),
            "ByType": dict(account_counts_by_type),
            "ActiveByType": dict(active_account_counts_by_type),
            "OrganizationalUnits": sorted(list(organizational_unit_names)),
        }

        return summary
