# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Network interface display formatting utilities."""

from typing import List

from rich.console import Console
from rich.table import Table

from telco_cli.types.network_interface import NetworkInterface


class NetworkInterfaceFormatter:
    """Formatter for network interface display."""

    def __init__(self, console: Console):
        self.console = console

    def get_server_icon(self, platform: str) -> str:
        """Get appropriate icon for server platform."""
        platform_lower = platform.lower()
        if "ubuntu" in platform_lower:
            return "🐧"
        elif "amazon" in platform_lower:
            return "☁️"
        elif "raspbian" in platform_lower:
            return "🍓"
        else:
            return "🖥️"

    def display_interface_table(
        self, server_name: str, instance_id: str, platform: str, interfaces: List[NetworkInterface]
    ) -> None:
        """Display network interface table for a single server."""
        server_icon = self.get_server_icon(platform)
        self.console.print(
            f"\n{server_icon} [bold yellow]{server_name}[/bold yellow] ({instance_id})"
        )

        if not interfaces:
            self.console.print("⚠️  [dim]Unable to retrieve interface details[/dim]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("🔌 Interface Name", style="cyan")
        table.add_column("📊 Status", style="green")
        table.add_column("🌐 IP Address", style="yellow")
        table.add_column("⚡ Speed", style="blue")
        table.add_column("🔧 Driver", style="magenta")
        table.add_column("🚀 SR-IOV", style="red")

        for interface in interfaces:
            table.add_row(
                interface.name,
                self._format_status(interface.status),
                self._format_ip_address(interface.ip_address or ""),
                self._format_speed(interface.speed or ""),
                self._format_driver(interface.driver or ""),
                self._format_sriov(interface.sriov_capability or ""),
            )

        self.console.print(table)

    def _format_status(self, status: str) -> str:
        """Format interface status with appropriate styling."""
        if status == "ACTIVE":
            return "[green]🟢 ACTIVE[/]"
        else:
            return "[dim]🔴 Inactive[/]"

    def _format_ip_address(self, ip_address: str) -> str:
        """Format IP address display."""
        return ip_address if ip_address else "➖"

    def _format_speed(self, speed: str) -> str:
        """Format speed display."""
        return speed if speed else "➖"

    def _format_driver(self, driver: str) -> str:
        """Format driver display."""
        return driver if driver else "❓ Unknown"

    def _format_sriov(self, sriov_capability: str) -> str:
        """Format SR-IOV capability with appropriate styling."""
        if not sriov_capability:
            return "[dim]❓ Unknown[/]"
        elif "Capable" in sriov_capability:
            return f"[green]✅ {sriov_capability}[/]"
        elif "Not Capable" in sriov_capability:
            return "[dim]❌ Not Capable[/]"
        else:
            return f"[dim]❓ {sriov_capability}[/]"
