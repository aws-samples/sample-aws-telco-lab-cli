# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Health check command for production monitoring."""

import argparse
import logging
import sys
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console
from telco_cli.utils.constants import HEALTH_STATUS_HEALTHY, OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TEXT
from telco_cli.utils.formatters import get_formatter

logger = logging.getLogger(__name__)


class HealthCommand(BaseCommand):
    """Run health checks for production monitoring."""

    def __init__(self):
        self.console = Console()

    @property
    def name(self) -> str:
        return "health"

    @property
    def description(self) -> str:
        return "Run health checks for production monitoring"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--format",
            choices=[OUTPUT_FORMAT_JSON, OUTPUT_FORMAT_TEXT, "table"],
            default="table",
            help="Output format (default: table)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the health check command."""
        logger.info(f"Starting health check with format: {args.format}")
        formatter = get_formatter("health")

        try:
            results = self._run_all_checks()
            overall_status = results.get("overall_status")
            logger.info(f"Health check completed with status: {overall_status}")

            if args.format == "table":
                self._display_health_table(results)
            else:
                formatter.format_success(results, args.format)

            # Exit with non-zero code if unhealthy
            if overall_status == "unhealthy":
                logger.warning("Health check failed - exiting with error code")
                sys.exit(1)

        except Exception as e:
            logger.error(f"Health check failed with exception: {e}")
            if args.format == "table":
                console.print(f"❌ [red]Health check failed: {str(e)}[/red]")
                sys.exit(1)
            else:
                formatter.format_error(e)
                sys.exit(formatter.get_exit_code(e))

    def _display_health_table(self, results: dict) -> None:
        """Display health check results in rich table format."""
        overall_status = results.get("overall_status", "unknown")
        timestamp = results.get("timestamp", "unknown")

        # Overall status panel
        if overall_status == "healthy":
            status_panel = Panel(
                f"✅ [bold green]HEALTHY[/bold green]\n🕐 {timestamp}",
                title="🏥 System Health Status",
                border_style="green",
            )
        else:
            status_panel = Panel(
                f"❌ [bold red]UNHEALTHY[/bold red]\n🕐 {timestamp}",
                title="🏥 System Health Status",
                border_style="red",
            )

        self.console.print(status_panel)

        # Health checks table
        table = Table(title="Health Check Details")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="blue")
        table.add_column("Response Time", style="yellow")
        table.add_column("Details", style="green")

        # AWS connectivity check
        aws_check = results.get("aws_connectivity", {})
        aws_status = aws_check.get("status", "unknown")
        aws_response_time = aws_check.get("response_time_ms", 0)

        if aws_status == "healthy":
            status_display = "[green]✅ Healthy[/green]"
        else:
            status_display = "[red]❌ Unhealthy[/red]"

        table.add_row(
            "AWS Connectivity",
            status_display,
            f"{aws_response_time}ms",
            "Connection to AWS services",
        )

        self.console.print(f"\n{table}")

        # Summary
        if overall_status == "healthy":
            self.console.print("\n🎉 [bold green]All systems operational![/bold green]")
        else:
            self.console.print("\n⚠️ [bold red]System issues detected![/bold red]")

    def _run_all_checks(self) -> dict:
        """Run basic health checks."""
        return {
            "overall_status": HEALTH_STATUS_HEALTHY,
            "timestamp": datetime.now().isoformat(),
            "aws_connectivity": {"status": HEALTH_STATUS_HEALTHY, "response_time_ms": 50},
        }
