# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Outpost utilization display formatting utilities."""

from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

from telco_cli.types.outpost_data import OutpostSummary, RegionalBreakdown


class OutpostUtilizationFormatter:
    """Formats Outpost utilization data for display."""

    def __init__(self, console: Console):
        self.console = console

    def display_summary_table(self, summaries: List[OutpostSummary]) -> None:
        """Display Outpost summaries in table format."""
        if not summaries:
            self.console.print("📭 [yellow]No Outpost data available.[/yellow]")
            return

        table = Table(title="🏢 Outpost Utilization Summary")
        table.add_column("Outpost ID", style="cyan")
        table.add_column("Name", style="yellow")
        table.add_column("Region", style="green")
        table.add_column("Assets", style="blue")
        table.add_column("Running", style="magenta")
        table.add_column("Utilization", style="red")

        for summary in summaries:
            utilization_color = self._get_utilization_color(summary.utilization_percentage)
            table.add_row(
                summary.outpost_id,
                summary.name,
                summary.region,
                str(summary.assets.total),
                str(summary.instances.running),
                f"[{utilization_color}]{summary.utilization_percentage:.1f}%[/]",
            )

        self.console.print(table)

    def display_regional_breakdown(self, breakdowns: List[RegionalBreakdown]) -> None:
        """Display regional breakdown in table format."""
        if not breakdowns:
            return

        self.console.print("\n🌍 [bold cyan]Regional Breakdown[/bold cyan]")

        table = Table()
        table.add_column("Region", style="cyan")
        table.add_column("Outposts", style="yellow")
        table.add_column("Total Capacity", style="blue")
        table.add_column("Used Capacity", style="magenta")
        table.add_column("Utilization", style="red")

        for breakdown in breakdowns:
            utilization_color = self._get_utilization_color(breakdown.utilization_percentage)
            table.add_row(
                breakdown.region,
                str(breakdown.outpost_count),
                str(breakdown.total_capacity),
                str(breakdown.used_capacity),
                f"[{utilization_color}]{breakdown.utilization_percentage:.1f}%[/]",
            )

        self.console.print(table)

    def display_summary_format(self, result: Dict[str, Any]) -> None:
        """Display results in summary format."""
        if not result.get("Success"):
            self.console.print(f"❌ [red]Error: {result.get('Error', 'Unknown error')}[/red]")
            return

        summary = result.get("Summary", {})
        self.console.print("📊 [bold cyan]Outpost Utilization Overview[/bold cyan]")
        self.console.print(f"Total Outposts: [yellow]{summary.get('total_outposts', 0)}[/yellow]")
        self.console.print(f"Total Capacity: [blue]{summary.get('total_capacity', 0)}[/blue]")
        self.console.print(f"Used Capacity: [magenta]{summary.get('used_capacity', 0)}[/magenta]")

        overall_util = summary.get("overall_utilization", 0)
        util_color = self._get_utilization_color(overall_util)
        self.console.print(f"Overall Utilization: [{util_color}]{overall_util:.1f}%[/]")

    @staticmethod
    def _get_utilization_color(percentage: float) -> str:
        """Get color based on utilization percentage."""
        if percentage >= 90:
            return "red"
        elif percentage >= 70:
            return "yellow"
        elif percentage >= 50:
            return "blue"
        else:
            return "green"
