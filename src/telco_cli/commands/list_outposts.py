# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""List Outposts Command implementation."""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.table import Table

from telco_cli.types.base_command import BaseCommand


class ListOutpostsCommand(BaseCommand):
    """List all AWS Outposts and their status."""

    def __init__(self):
        self.console = Console()

    @property
    def name(self) -> str:
        return "list-outposts"

    @property
    def description(self) -> str:
        return "List all AWS Outposts and their status"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--region-filter", help="Filter by region (e.g., us-west-2)")
        parser.add_argument(
            "--status-filter",
            choices=["ACTIVE", "PENDING", "PROVISIONING", "INACTIVE", "DELETING"],
            help="Filter by Outpost status",
        )
        parser.add_argument(
            "--include-capacity", action="store_true", help="Include detailed capacity information"
        )
        parser.add_argument(
            "--output",
            choices=["json", "table", "summary"],
            default="json",
            help="Output format (default: json)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the list outposts command."""
        try:
            self.console.print("📋 Listing AWS Outposts...")
            result = self._list_outposts(args)

            if args.output == "table":
                self._print_table_format(result)
            elif args.output == "summary":
                self._print_summary_format(result)
            else:
                print(json.dumps(result, indent=2))

        except Exception as e:
            self.console.print(f"❌ Failed to list outposts: {str(e)}", style="bold red")
            error_result = {"Error": {"Code": "OutpostListError", "Message": str(e)}}
            print(json.dumps(error_result, indent=2), file=sys.stderr)
            sys.exit(1)

    def _list_outposts(self, args: argparse.Namespace) -> Dict[str, Any]:
        """List all AWS Outposts with detailed information."""
        try:
            outposts_client = boto3.client("outposts")
            ec2_client = boto3.client("ec2")

            # Get all Outposts
            paginator = outposts_client.get_paginator("list_outposts")
            all_outposts = []

            for page in paginator.paginate():
                all_outposts.extend(page["Outposts"])

            # Process each Outpost
            processed_outposts = []

            for outpost in all_outposts:
                # Apply region filter
                if args.region_filter and not outpost["AvailabilityZone"].startswith(
                    args.region_filter
                ):
                    continue

                # Apply status filter
                if args.status_filter and outpost["LifeCycleStatus"] != args.status_filter:
                    continue

                # Get basic Outpost information with safe access
                outpost_info = {
                    "OutpostId": outpost.get("OutpostId", "Unknown"),
                    "OutpostArn": outpost.get("OutpostArn", "Unknown"),
                    "Name": outpost.get("Name", "Unnamed"),
                    "Description": outpost.get("Description", ""),
                    "LifeCycleStatus": outpost.get("LifeCycleStatus", "Unknown"),
                    "AvailabilityZone": outpost.get("AvailabilityZone", "Unknown"),
                    "AvailabilityZoneId": outpost.get("AvailabilityZoneId", "Unknown"),
                    "SiteId": outpost.get("SiteId", "Unknown"),
                    "SiteArn": outpost.get("SiteArn", "Unknown"),
                    "SupportedHardwareType": outpost.get("SupportedHardwareType", "Unknown"),
                    "Tags": {
                        tag.get("Key", ""): tag.get("Value", "")
                        for tag in outpost.get("Tags", [])
                        if isinstance(tag, dict)
                    },
                }

                # Get capacity information if requested
                if args.include_capacity:
                    capacity_info = self._get_outpost_capacity(
                        outposts_client, ec2_client, outpost["OutpostId"]
                    )
                    outpost_info["Capacity"] = capacity_info

                # Get dedicated hosts count (simplified)
                try:
                    hosts_info = self._get_outpost_hosts_info(ec2_client, outpost["OutpostArn"])
                    outpost_info["DedicatedHosts"] = hosts_info
                except Exception:
                    outpost_info["DedicatedHosts"] = {
                        "TotalHosts": 0,
                        "AvailableHosts": 0,
                        "AssignedHosts": 0,
                    }

                processed_outposts.append(outpost_info)

            # Sort by Outpost ID
            processed_outposts.sort(key=lambda x: x["OutpostId"])

            # Generate summary
            summary = self._generate_outpost_summary(processed_outposts)

            return {
                "Success": True,
                "Outposts": processed_outposts,
                "Summary": summary,
                "FilteredBy": {"Region": args.region_filter, "Status": args.status_filter},
                "LastUpdated": datetime.now(timezone.utc).isoformat(),
            }

        except ClientError as e:
            return {
                "Success": False,
                "Error": {
                    "Code": "AWSError",
                    "Message": f"AWS error: {e.response['Error']['Message']}",
                },
            }

    def _safe_get_int(self, value) -> int:
        """Safely convert value to int."""
        if isinstance(value, int):
            return value
        elif isinstance(value, (list, dict)):
            return len(value) if value else 0
        else:
            return 0

    def _get_outpost_capacity(self, outposts_client, ec2_client, outpost_id: str) -> Dict[str, Any]:
        """Get capacity information for an Outpost."""
        try:
            # Get Outpost instance types
            response = outposts_client.get_outpost_instance_types(OutpostId=outpost_id)
            instance_types = response.get("InstanceTypes", [])

            capacity_info = {
                "SupportedInstanceTypes": [it["InstanceType"] for it in instance_types],
                "InstanceTypeCount": len(instance_types),
                "CapacityDetails": instance_types,
            }

            return capacity_info

        except Exception as e:
            return {"Error": f"Could not retrieve capacity information: {str(e)}"}

    def _get_outpost_hosts_info(self, ec2_client, outpost_arn: str) -> Dict[str, Any]:
        """Get dedicated hosts information for an Outpost."""
        try:
            # Get dedicated hosts for this Outpost using filters
            response = ec2_client.describe_hosts(
                Filters=[{"Name": "outpost-arn", "Values": [outpost_arn]}]
            )
            outpost_hosts = response["Hosts"]

            # Categorize hosts
            available_hosts = [host for host in outpost_hosts if host["State"] == "available"]
            assigned_hosts = []

            for host in outpost_hosts:
                tags = {tag["Key"]: tag["Value"] for tag in host.get("Tags", [])}
                if tags.get("AssignedTo"):
                    assigned_hosts.append(host)

            return {
                "TotalHosts": len(outpost_hosts),
                "AvailableHosts": len(available_hosts),
                "AssignedHosts": len(assigned_hosts),
                "HostDetails": [
                    {
                        "HostId": host["HostId"],
                        "InstanceType": host.get("HostProperties", {}).get(
                            "InstanceType", "Unknown"
                        ),
                        "State": host["State"],
                        "AssignedTo": tags.get("AssignedTo"),
                    }
                    for host in outpost_hosts
                ],
            }

        except Exception as e:
            return {"Error": f"Could not retrieve hosts information: {str(e)}"}

    def _generate_outpost_summary(self, outposts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics for Outposts."""
        if not outposts:
            return {}

        # Combine loops for better performance
        status_counts: Dict[str, int] = {}
        region_counts: Dict[str, int] = {}
        total_hosts = 0
        available_hosts = 0
        assigned_hosts = 0

        for outpost in outposts:
            # Count by status
            status = outpost["LifeCycleStatus"]
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by region
            az = outpost["AvailabilityZone"]
            region = az[:-1] if len(az) > 1 and az[-1].isalpha() else az
            region_counts[region] = region_counts.get(region, 0) + 1

            # Count hosts
            hosts_info = outpost.get("DedicatedHosts", {})
            if isinstance(hosts_info, dict):
                total_hosts += hosts_info.get("TotalHosts", 0)
                available_hosts += hosts_info.get("AvailableHosts", 0)
                assigned_hosts += hosts_info.get("AssignedHosts", 0)

        return {
            "TotalOutposts": len(outposts),
            "ByStatus": status_counts,
            "ByRegion": region_counts,
            "TotalDedicatedHosts": total_hosts,
            "AvailableDedicatedHosts": available_hosts,
            "AssignedDedicatedHosts": assigned_hosts,
            "HostUtilization": (
                round((assigned_hosts / total_hosts) * 100, 1) if total_hosts > 0 else 0
            ),
        }

    def _print_table_format(self, result: Dict[str, Any]) -> None:
        """Print results in table format using rich."""
        if not result.get("Success"):
            self.console.print(
                f"❌ Error: {result.get('Error', {}).get('Message', 'Unknown error')}",
                style="bold red",
            )
            return

        outposts = result.get("Outposts", [])
        if not outposts:
            self.console.print("📭 No Outposts found.", style="yellow")
            return

        # Create rich table
        table = Table(title="🏢 AWS Outposts")
        table.add_column("Outpost ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("AZ", style="blue")
        table.add_column("Hosts", justify="right", style="yellow")
        table.add_column("Available", justify="right", style="green")

        # Add rows
        for outpost in outposts:
            hosts_info = outpost.get("DedicatedHosts", {})
            total_hosts = hosts_info.get("TotalHosts", 0)
            available_hosts = hosts_info.get("AvailableHosts", 0)

            # Color code status
            status = outpost["LifeCycleStatus"]
            if status == "ACTIVE":
                status_display = f"[green]{status}[/green]"
            elif status in ["PENDING", "PROVISIONING"]:
                status_display = f"[yellow]{status}[/yellow]"
            elif status == "INACTIVE":
                status_display = f"[red]{status}[/red]"
            else:
                status_display = status

            table.add_row(
                outpost["OutpostId"],
                outpost["Name"][:30] + "..." if len(outpost["Name"]) > 30 else outpost["Name"],
                status_display,
                outpost["AvailabilityZone"],
                str(total_hosts),
                str(available_hosts),
            )

        self.console.print(table)

        # Print summary
        summary = result.get("Summary", {})
        self.console.print(
            f"\n📊 [bold]Summary:[/bold] {summary.get('TotalOutposts', 0)} Outposts, {summary.get('TotalDedicatedHosts', 0)} total hosts ([green]{summary.get('AvailableDedicatedHosts', 0)} available[/green])"
        )

    def _print_summary_format(self, result: Dict[str, Any]) -> None:
        """Print results in summary format using rich."""
        if not result.get("Success"):
            self.console.print(
                f"❌ Error: {result.get('Error', {}).get('Message', 'Unknown error')}",
                style="bold red",
            )
            return

        summary = result.get("Summary", {})

        self.console.print("🏢 [bold cyan]AWS Outposts Summary[/bold cyan]")
        self.console.print("=" * 30)
        self.console.print(
            f"📊 Total Outposts: [bold yellow]{summary.get('TotalOutposts', 0)}[/bold yellow]"
        )
        self.console.print()

        self.console.print("📈 [bold]By Status:[/bold]")
        for status, count in summary.get("ByStatus", {}).items():
            if status == "ACTIVE":
                self.console.print(f"  [green]{status}[/green]: {count}")
            elif status in ["PENDING", "PROVISIONING"]:
                self.console.print(f"  [yellow]{status}[/yellow]: {count}")
            elif status == "INACTIVE":
                self.console.print(f"  [red]{status}[/red]: {count}")
            else:
                self.console.print(f"  {status}: {count}")
        self.console.print()

        self.console.print("🌍 [bold]By Region:[/bold]")
        for region, count in summary.get("ByRegion", {}).items():
            self.console.print(f"  [blue]{region}[/blue]: {count}")
        self.console.print()

        self.console.print("🖥️ [bold]Dedicated Hosts:[/bold]")
        self.console.print(f"  Total: [bold]{summary.get('TotalDedicatedHosts', 0)}[/bold]")
        self.console.print(
            f"  Available: [green]{summary.get('AvailableDedicatedHosts', 0)}[/green]"
        )
        self.console.print(
            f"  Assigned: [yellow]{summary.get('AssignedDedicatedHosts', 0)}[/yellow]"
        )
        self.console.print(f"  Utilization: [cyan]{summary.get('HostUtilization', 0)}%[/cyan]")
