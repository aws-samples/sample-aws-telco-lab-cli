# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""List Test Servers Command implementation."""

import argparse
import json
from typing import Any, Dict, List

from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.services.instance_service import InstanceService
from telco_cli.types.base_command import BaseCommand
from telco_cli.types.network_interface import NetworkInterface
from telco_cli.utils import get_logger
from telco_cli.utils.formatters import format_status_display
from telco_cli.utils.network_commands import NETWORK_INTERFACE_COMMAND
from telco_cli.utils.network_formatter import NetworkInterfaceFormatter
from telco_cli.utils.network_parser import NetworkInterfaceParser

logger = get_logger(__name__)


class ListTestServersCommand(BaseCommand):
    """List all SSM managed test servers."""

    def __init__(self):
        self.console = Console()
        self._instance_service = None
        self.network_formatter = NetworkInterfaceFormatter(self.console)
        self.network_parser = NetworkInterfaceParser()

    @property
    def instance_service(self) -> InstanceService:
        """Lazy initialization of instance service."""
        if self._instance_service is None:
            self._instance_service = InstanceService()
        return self._instance_service

    @property
    def name(self) -> str:
        return "list-test-servers"

    @property
    def description(self) -> str:
        return "List all SSM managed test servers"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--status",
            choices=["Online", "Offline", "All"],
            default="All",
            help="Filter servers by SSM status",
        )
        parser.add_argument(
            "--output",
            choices=["json", "table"],
            default="table",
            help="Output format (default: table)",
        )
        parser.add_argument(
            "--show-nic-detail",
            action="store_true",
            help="Show detailed network interface information for online servers",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the list test servers command."""
        try:
            logger.info(f"Listing SSM managed servers with status filter: {args.status}")
            servers = self.instance_service.list_managed_instances(args.status)

            if args.output == "table":
                self._display_servers_table(servers)
                if args.show_nic_detail:
                    self._display_nic_details(servers)
            else:
                if args.show_nic_detail:
                    servers = self._enrich_with_nic_details(servers)
                self._display_servers_json(servers)

        except ClientError as e:
            logger.error(f"AWS error listing SSM instances: {e}")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, str(e))
        except Exception as e:
            logger.exception("Failed to list test servers")
            raise TelcoCLIException(ErrorCode.UNKNOWN_ERROR, str(e))

    def _display_servers_table(self, servers: List[Dict[str, Any]]) -> None:
        """Display servers in a rich table format."""
        if not servers:
            self.console.print("📭 [yellow]No SSM managed servers found.[/yellow]")
            return

        self.console.print(
            f"\n🖥️ [bold cyan]Found {len(servers)} SSM managed server(s):[/bold cyan]"
        )

        table = Table(title="SSM Managed Test Servers")
        table.add_column("Instance ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("Platform", style="green")
        table.add_column("IP Address", style="magenta")

        for server in servers:
            status = server.get("PingStatus", "Unknown")
            table.add_row(
                server.get("InstanceId", "Unknown"),
                server.get("Name", "Unknown"),
                format_status_display(status),
                server.get("PlatformName", "Unknown"),
                server.get("IPAddress", "Unknown"),
            )

        self.console.print(table)

    def _display_servers_json(self, servers: List[Dict[str, Any]]) -> None:
        """Display servers in JSON format."""
        if not servers:
            self.console.print("📭 [yellow]No SSM managed servers found.[/yellow]")
            return

        self.console.print(
            f"\n🖥️ [bold cyan]Found {len(servers)} SSM managed server(s):[/bold cyan]"
        )
        print(json.dumps(servers, indent=2, default=str))

    def _get_nic_details(self, instance_id: str) -> List[NetworkInterface]:
        """Get network interface details for a specific instance via SSM."""
        try:
            result = self.instance_service.ssm_service.send_command(
                instance_id, NETWORK_INTERFACE_COMMAND
            )
            if not result:
                return []

            return self.network_parser.parse_interface_output(result)

        except Exception as e:
            logger.warning(f"Failed to get NIC details for {instance_id}: {e}")
            return []

    def _display_nic_details(self, servers: List[Dict[str, Any]]) -> None:
        """Display detailed network interface information for servers."""
        online_servers = [s for s in servers if s.get("PingStatus") == "Online"]

        if not online_servers:
            self.console.print(
                "\n⚠️  [yellow]No servers available for NIC detail retrieval.[/yellow]"
            )
            return

        self.console.print("\n[bold cyan]🌐 Network Interface Details[/bold cyan]")

        for server in online_servers:
            instance_id = server.get("InstanceId", "Unknown")
            server_name = server.get("Name", instance_id)
            platform = server.get("PlatformName", "Unknown")

            interfaces = self._get_nic_details(instance_id)
            self.network_formatter.display_interface_table(
                server_name, instance_id, platform, interfaces
            )

    def _enrich_with_nic_details(self, servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich server data with NIC details for JSON output."""
        enriched_servers = []

        for server in servers:
            enriched_server = server.copy()

            if server.get("PingStatus") == "Online":
                instance_id = server.get("InstanceId")
                if instance_id:
                    interfaces = self._get_nic_details(instance_id)
                    enriched_server["network_interfaces"] = [
                        {
                            "name": iface.name,
                            "status": iface.status,
                            "ip_address": iface.ip_address,
                            "speed": iface.speed,
                            "driver": iface.driver,
                            "sriov_capability": iface.sriov_capability,
                        }
                        for iface in interfaces
                    ]

            enriched_servers.append(enriched_server)

        return enriched_servers
