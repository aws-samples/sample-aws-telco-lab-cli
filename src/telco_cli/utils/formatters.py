# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Output formatting utilities for TelcoCLI."""

import json
from typing import Any, Dict, Union

from botocore.exceptions import ClientError, NoCredentialsError
from rich.table import Table

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.utils.account_constants import MAX_OU_DISPLAY_COUNT
from telco_cli.utils.constants import (
    HEALTH_STATUS_UNHEALTHY,
    OUTPUT_FORMAT_JSON,
    OUTPUT_FORMAT_SUMMARY,
    OUTPUT_FORMAT_TABLE,
    OUTPUT_FORMAT_TEXT,
)
from telco_cli.utils.logging import console, console_error


class OutputFormatter:
    """Base class for output formatting with unified error handling."""

    def format_error(self, error: Union[Dict[str, Any], TelcoCLIException, Exception]) -> None:
        """Format and print error output with unified handling."""
        error_data = self._extract_error_data(error)
        console_error.print(json.dumps(error_data, indent=2))

    def format_success(self, data: Dict[str, Any], format_type: str = OUTPUT_FORMAT_JSON) -> None:
        """Format and print success output."""
        if format_type == OUTPUT_FORMAT_JSON:
            console.print(json.dumps(data, indent=2))
        else:
            # Default to JSON if format not supported
            console.print(json.dumps(data, indent=2))

    def _extract_error_data(
        self, error: Union[Dict[str, Any], TelcoCLIException, Exception]
    ) -> Dict[str, Any]:
        """Extract error data from various error types."""
        if isinstance(error, dict):
            return error

        if isinstance(error, TelcoCLIException):
            return {
                "Error": {
                    "Code": error.error_code.name,
                    "Message": str(error),
                    "ExitCode": error.exit_code,
                }
            }

        if isinstance(error, NoCredentialsError):
            return {
                "Error": {
                    "Code": "NoCredentialsError",
                    "Message": "AWS credentials not configured",
                    "ExitCode": ErrorCode.AWS_CONNECTION_ERROR.value,
                }
            }

        if isinstance(error, ClientError):
            error_code = error.response.get("Error", {}).get("Code", "UnknownAWSError")
            error_message = error.response.get("Error", {}).get("Message", str(error))
            return {
                "Error": {
                    "Code": error_code,
                    "Message": f"AWS service error: {error_message}",
                    "ExitCode": ErrorCode.AWS_CONNECTION_ERROR.value,
                }
            }

        return {
            "Error": {
                "Code": "UnexpectedError",
                "Message": str(error),
                "ExitCode": ErrorCode.UNKNOWN_ERROR.value,
            }
        }

    def get_exit_code(self, error: Union[Dict[str, Any], TelcoCLIException, Exception]) -> int:
        """Extract exit code from error."""
        if isinstance(error, TelcoCLIException):
            return error.exit_code

        if isinstance(error, (NoCredentialsError, ClientError)):
            return ErrorCode.AWS_CONNECTION_ERROR.value

        if isinstance(error, dict):
            return error.get("Error", {}).get("ExitCode", ErrorCode.UNKNOWN_ERROR.value)

        return ErrorCode.UNKNOWN_ERROR.value


class HealthCheckOutputFormatter(OutputFormatter):
    """Formatter for health check output."""

    def format_success(self, data: Dict[str, Any], format_type: str = OUTPUT_FORMAT_JSON) -> None:
        """Format health check output."""
        if format_type == OUTPUT_FORMAT_TEXT:
            self._print_text_format(data)
        else:
            console.print(json.dumps(data, indent=2))

    def format_error(self, error: Union[Dict[str, Any], TelcoCLIException, Exception]) -> None:
        """Format health check error with unhealthy status."""
        error_data = self._extract_error_data(error)

        # Add health-specific context
        health_error = {
            "overall_status": HEALTH_STATUS_UNHEALTHY,
            "error": error_data["Error"]["Message"],
            "error_code": error_data["Error"]["Code"],
        }

        console_error.print(json.dumps(health_error, indent=2))

    def _print_text_format(self, results: Dict[str, Any]) -> None:
        """Print health results in human-readable text format."""
        console.print(f"Overall Status: {results['overall_status'].upper()}")
        console.print(f"Timestamp: {results['timestamp']}")
        console.print()

        for check_name, check_result in results.items():
            if check_name in ["overall_status", "timestamp"]:
                continue

            if isinstance(check_result, dict):
                status = check_result.get("status", "unknown")
                console.print(f"{check_name.replace('_', ' ').title()}: {status.upper()}")

                if "response_time_ms" in check_result:
                    console.print(f"  Response Time: {check_result['response_time_ms']}ms")

                if "error" in check_result:
                    console.print(f"  Error: {check_result['error']}")

                if "message" in check_result:
                    console.print(f"  Message: {check_result['message']}")

                console.print()


class AccountsOutputFormatter(OutputFormatter):
    """Formatter for accounts list output."""

    def format_success(self, data: Dict[str, Any], format_type: str = OUTPUT_FORMAT_JSON) -> None:
        """Format accounts list output."""
        if format_type == OUTPUT_FORMAT_TABLE:
            self._print_table_format(data)
        elif format_type == OUTPUT_FORMAT_SUMMARY:
            self._print_summary_format(data)
        else:
            console.print(json.dumps(data, indent=2))

    def _print_table_format(self, result: Dict[str, Any]) -> None:
        """Print results in table format using rich."""
        if not result.get("Success"):
            console.print("❌ Error: Failed to retrieve accounts", style="bold red")
            return

        accounts = result.get("Accounts", [])
        if not accounts:
            console.print("📭 No accounts found.", style="yellow")
            return

        # Create rich table
        table = Table(title="🏢 AWS Organization Accounts")
        table.add_column("Account ID", style="cyan", no_wrap=True)
        table.add_column("Account Type", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Account Name", style="blue")

        # Add rows with color coding
        for account in accounts:
            account_type = account.get("AccountType", "Unknown")
            status = account.get("Status", "Unknown")

            # Color code account types
            if account_type == "management":
                type_display = f"[bold yellow]{account_type}[/bold yellow]"
            elif account_type == "security":
                type_display = f"[bold red]{account_type}[/bold red]"
            elif account_type == "partner":
                type_display = f"[bold green]{account_type}[/bold green]"
            else:
                type_display = account_type

            # Color code status
            if status == "ACTIVE":
                status_display = f"[green]{status}[/green]"
            elif status == "SUSPENDED":
                status_display = f"[red]{status}[/red]"
            else:
                status_display = status

            # Truncate long account names
            account_name = account.get("AccountName", "Unknown")
            if len(account_name) > 50:
                account_name = account_name[:47] + "..."

            table.add_row(account["AccountId"], type_display, status_display, account_name)

        console.print(table)

        # Print enhanced summary
        summary = result.get("Summary", {})
        console.print("\n📊 [bold]Summary:[/bold]")
        console.print(
            f"Total Accounts: [bold yellow]{summary.get('TotalAccounts', 0)}[/bold yellow]"
        )

        by_status = summary.get("ByStatus", {})
        if by_status:
            console.print("By Status: ", end="")
            status_parts = []
            for status, count in by_status.items():
                if status == "ACTIVE":
                    status_parts.append(f"[green]{status}: {count}[/green]")
                elif status == "SUSPENDED":
                    status_parts.append(f"[red]{status}: {count}[/red]")
                else:
                    status_parts.append(f"{status}: {count}")
            console.print(", ".join(status_parts))

        by_type = summary.get("ByType", {})
        if by_type:
            console.print("By Type: ", end="")
            type_parts = []
            for acc_type, count in by_type.items():
                if acc_type == "management":
                    type_parts.append(f"[bold yellow]{acc_type}: {count}[/bold yellow]")
                elif acc_type == "security":
                    type_parts.append(f"[bold red]{acc_type}: {count}[/bold red]")
                elif acc_type == "partner":
                    type_parts.append(f"[bold green]{acc_type}: {count}[/bold green]")
                else:
                    type_parts.append(f"{acc_type}: {count}")
            console.print(", ".join(type_parts))

    def _print_summary_format(self, result: Dict[str, Any]) -> None:
        """Print results in summary format using rich."""
        if not result.get("Success"):
            console.print("❌ Error: Failed to retrieve accounts", style="bold red")
            return

        summary = result.get("Summary", {})

        console.print("🏢 [bold cyan]AWS Organizations / Control Tower Summary[/bold cyan]")
        console.print("=" * 50)
        console.print(
            f"📊 Total Accounts: [bold yellow]{summary.get('TotalAccounts', 0)}[/bold yellow]"
        )
        console.print()

        console.print("📈 [bold]Account Status:[/bold]")
        for status, count in summary.get("ByStatus", {}).items():
            if status == "ACTIVE":
                console.print(f"  [green]{status}[/green]: {count}")
            elif status == "SUSPENDED":
                console.print(f"  [red]{status}[/red]: {count}")
            else:
                console.print(f"  {status}: {count}")
        console.print()

        console.print("🏷️ [bold]Account Types:[/bold]")
        for account_type, count in summary.get("ByType", {}).items():
            active_count = summary.get("ActiveByType", {}).get(account_type, 0)
            if account_type == "management":
                console.print(
                    f"  [bold yellow]{account_type.title()}[/bold yellow]: {count} total ([green]{active_count} active[/green])"
                )
            elif account_type == "security":
                console.print(
                    f"  [bold red]{account_type.title()}[/bold red]: {count} total ([green]{active_count} active[/green])"
                )
            elif account_type == "partner":
                console.print(
                    f"  [bold green]{account_type.title()}[/bold green]: {count} total ([green]{active_count} active[/green])"
                )
            else:
                console.print(
                    f"  [blue]{account_type.title()}[/blue]: {count} total ([green]{active_count} active[/green])"
                )
        console.print()

        if summary.get("OrganizationalUnits"):
            console.print(
                f"🏗️ [bold]Organizational Units:[/bold] {len(summary.get('OrganizationalUnits', []))}"
            )
            for ou in summary.get("OrganizationalUnits", [])[:MAX_OU_DISPLAY_COUNT]:
                console.print(f"  - [cyan]{ou}[/cyan]")
            if len(summary.get("OrganizationalUnits", [])) > MAX_OU_DISPLAY_COUNT:
                console.print(
                    f"  ... and [yellow]{len(summary.get('OrganizationalUnits', [])) - MAX_OU_DISPLAY_COUNT} more[/yellow]"
                )


def format_status_display(status: str) -> str:
    """Format status with color coding."""
    if status == "Online":
        return f"[green]{status}[/green]"
    elif status in ["Offline", "ConnectionLost"]:
        return f"[red]{status}[/red]"
    else:
        return f"[yellow]{status}[/yellow]"


def get_formatter(formatter_type: str) -> OutputFormatter:
    """Get appropriate formatter instance."""
    formatters = {
        "health": HealthCheckOutputFormatter(),
        "accounts": AccountsOutputFormatter(),
    }
    return formatters.get(formatter_type, OutputFormatter())
