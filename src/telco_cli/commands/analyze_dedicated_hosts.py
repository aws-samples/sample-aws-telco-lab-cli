# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Analyze Dedicated Hosts Command implementation."""

import argparse
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger


class AnalyzeDedicatedHostsCommand(BaseCommand):
    """Command to analyze dedicated hosts across regions with filtering and assignment tracking."""

    @property
    def name(self) -> str:
        return "analyze-dedicated-hosts"

    @property
    def description(self) -> str:
        return "Analyze dedicated hosts with assignment tracking and filtering options"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument("--region", help="AWS region to analyze")
        parser.add_argument(
            "--all-regions", action="store_true", help="Analyze hosts across all regions"
        )
        parser.add_argument("--partner", help="Filter by partner name")
        parser.add_argument("--assigned-only", action="store_true", help="Show only assigned hosts")
        parser.add_argument(
            "--unassigned-only", action="store_true", help="Show only unassigned hosts"
        )
        parser.add_argument("--outpost-id", help="Filter by specific Outpost ID")
        parser.add_argument("--instance-type", help="Filter by instance type")
        parser.add_argument(
            "--state",
            choices=["available", "under-assessment", "permanent-failure", "released"],
            help="Filter by host state",
        )
        parser.add_argument(
            "--format", choices=["table", "json", "csv"], default="table", help="Output format"
        )

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register the command with the argument parser."""
        self.add_arguments(parser)

    def run(self, args: argparse.Namespace) -> None:
        """Run the command."""
        self.execute(args)

    def execute(self, args: argparse.Namespace) -> int:
        """Execute the analyze dedicated hosts command."""
        logger = get_logger(__name__)

        try:
            # Determine regions to analyze
            if args.all_regions:
                regions = self._get_all_regions()
            else:
                # Use specified region or default to us-east-1
                region = args.region or "us-east-1"
                regions = [region]

            all_hosts_data = []

            # Analyze each region
            for region in regions:
                logger.info(f"Analyzing dedicated hosts in region: {region}")
                try:
                    region_data = self._analyze_region(region, args)
                    if region_data:
                        all_hosts_data.extend(region_data)
                except TelcoCLIException:
                    raise
                except Exception as e:
                    logger.warning(f"Failed to analyze region {region}: {str(e)}")
                    continue

            if not all_hosts_data:
                console.print("📭 [yellow]No dedicated hosts found matching the criteria.[/yellow]")
                return 0

            # Apply additional filters
            filtered_data = self._apply_filters(all_hosts_data, args)

            if not filtered_data:
                console.print(
                    "🔍 [yellow]No dedicated hosts found after applying filters.[/yellow]"
                )
                return 0

            # Display results
            self._display_results(filtered_data, args)
            return 0

        except TelcoCLIException:
            raise
        except ClientError as e:
            logger.error(f"AWS API error: {e.response['Error']['Message']}")
            raise TelcoCLIException(
                ErrorCode.AWS_SERVICE_ERROR, f"AWS error: {e.response['Error']['Message']}"
            )
        except Exception as e:
            logger.error(f"Error analyzing dedicated hosts: {str(e)}")
            raise TelcoCLIException(
                ErrorCode.AWS_SERVICE_ERROR, f"Failed to analyze dedicated hosts: {str(e)}"
            )

    def _get_all_regions(self) -> List[str]:
        """Get all AWS regions."""
        try:
            ec2_client = boto3.client("ec2")
            response = ec2_client.describe_regions()
            return [region["RegionName"] for region in response["Regions"]]
        except ClientError as e:
            raise TelcoCLIException(
                ErrorCode.AWS_SERVICE_ERROR, f"AWS error: {e.response['Error']['Message']}"
            )
        except Exception as e:
            raise TelcoCLIException(ErrorCode.AWS_SERVICE_ERROR, f"Failed to get regions: {str(e)}")

    def _analyze_region(self, region: str, args: argparse.Namespace) -> List[Dict[str, Any]]:
        """Analyze dedicated hosts in a specific region."""
        try:
            ec2_client = boto3.client("ec2", region_name=region)

            # Get all dedicated hosts
            response = ec2_client.describe_hosts()
            all_hosts = response.get("Hosts", [])

            if not all_hosts:
                return []

            analyzed_hosts = []

            for host in all_hosts:
                try:
                    # Get host tags
                    tags = {tag["Key"]: tag["Value"] for tag in host.get("Tags", [])}

                    # Determine assignment status
                    assigned_to = tags.get("AssignedTo")
                    partner = tags.get("Partner")
                    is_assigned = bool(assigned_to)

                    # Check if it's an Outpost host
                    outpost_arn = host.get("OutpostArn")
                    outpost_id = outpost_arn.split("/")[-1] if outpost_arn else None

                    # Collect host information
                    host_analysis = {
                        "HostId": host["HostId"],
                        "InstanceType": host.get("HostProperties", {}).get("InstanceType"),
                        "AvailabilityZone": host["AvailabilityZone"],
                        "State": host["State"],
                        "Region": region,
                        "IsAssigned": is_assigned,
                        "AssignedTo": assigned_to,
                        "Partner": partner,
                        "OutpostId": outpost_id,
                        "OutpostArn": outpost_arn,
                        "AllTags": tags,
                        "HostRecovery": host.get("HostRecovery", "off"),
                        "AutoPlacement": host.get("AutoPlacement", "off"),
                    }

                    analyzed_hosts.append(host_analysis)

                except Exception as e:
                    get_logger(__name__).warning(
                        f"Error analyzing host {host.get('HostId', 'unknown')}: {str(e)}"
                    )
                    continue

            return analyzed_hosts

        except ClientError as e:
            raise TelcoCLIException(
                ErrorCode.AWS_SERVICE_ERROR,
                f"AWS error in region {region}: {e.response['Error']['Message']}",
            )
        except Exception as e:
            raise TelcoCLIException(
                ErrorCode.AWS_SERVICE_ERROR, f"Failed to analyze region {region}: {str(e)}"
            )

    def _apply_filters(
        self, hosts_data: List[Dict[str, Any]], args: argparse.Namespace
    ) -> List[Dict[str, Any]]:
        """Apply filters to the hosts data."""
        filtered_data = hosts_data

        # Filter by partner
        if args.partner:
            filtered_data = [
                host
                for host in filtered_data
                if (host.get("AssignedTo") and args.partner.lower() in host["AssignedTo"].lower())
                or (host.get("Partner") and args.partner.lower() in host["Partner"].lower())
            ]

        # Filter by assignment status
        if args.assigned_only:
            filtered_data = [host for host in filtered_data if host["IsAssigned"]]
        elif args.unassigned_only:
            filtered_data = [host for host in filtered_data if not host["IsAssigned"]]

        # Filter by outpost ID
        if args.outpost_id:
            filtered_data = [
                host for host in filtered_data if host.get("OutpostId") == args.outpost_id
            ]

        # Filter by instance type
        if args.instance_type:
            filtered_data = [
                host for host in filtered_data if host["InstanceType"] == args.instance_type
            ]

        # Filter by state
        if args.state:
            filtered_data = [host for host in filtered_data if host["State"] == args.state]

        return filtered_data

    def _display_results(self, hosts_data: List[Dict[str, Any]], args: argparse.Namespace) -> None:
        """Display the analysis results."""
        if args.format == "json":
            self._display_json(hosts_data)
        elif args.format == "csv":
            self._display_csv(hosts_data)
        else:
            self._display_table(hosts_data)

    def _display_table(self, hosts_data: List[Dict[str, Any]]) -> None:
        """Display results in table format."""
        from rich.table import Table

        table = Table(title="Dedicated Hosts Analysis")

        # Add columns
        table.add_column("Host ID", style="cyan")
        table.add_column("Region", style="magenta")
        table.add_column("Instance Type", style="green")
        table.add_column("AZ", style="yellow")
        table.add_column("State", style="blue")
        table.add_column("Assigned", style="red")
        table.add_column("Partner", style="white")
        table.add_column("Outpost ID", style="cyan")

        # Add rows
        for host in hosts_data:
            assigned_status = "✓" if host["IsAssigned"] else "✗"
            partner_info = host.get("AssignedTo") or host.get("Partner") or "-"
            outpost_info = host.get("OutpostId") or "-"

            table.add_row(
                host["HostId"],
                host["Region"],
                host["InstanceType"],
                host["AvailabilityZone"],
                host["State"],
                assigned_status,
                partner_info,
                outpost_info,
            )

        console.print(table)

        # Print enhanced summary
        total_hosts = len(hosts_data)
        assigned_hosts = sum(1 for host in hosts_data if host["IsAssigned"])
        unassigned_hosts = total_hosts - assigned_hosts
        utilization = (assigned_hosts / total_hosts * 100) if total_hosts > 0 else 0

        console.print("\n📊 [bold cyan]Summary:[/bold cyan]")
        console.print(f"🖥️ Total Hosts: [bold yellow]{total_hosts}[/bold yellow]")
        console.print(f"🔄 Assigned: [yellow]{assigned_hosts}[/yellow]")
        console.print(f"✅ Available: [green]{unassigned_hosts}[/green]")

        # Color-coded utilization
        if utilization >= 80:
            util_color = "red"
        elif utilization >= 60:
            util_color = "yellow"
        else:
            util_color = "green"
        console.print(f"📈 Utilization: [{util_color}]{utilization:.1f}%[/{util_color}]")

    def _display_json(self, hosts_data: List[Dict[str, Any]]) -> None:
        """Display results in JSON format."""
        import json

        console.print(json.dumps(hosts_data, indent=2, default=str))

    def _display_csv(self, hosts_data: List[Dict[str, Any]]) -> None:
        """Display results in CSV format."""
        import csv
        import sys

        if not hosts_data:
            return

        fieldnames = [
            "HostId",
            "Region",
            "InstanceType",
            "AvailabilityZone",
            "State",
            "IsAssigned",
            "AssignedTo",
            "Partner",
            "OutpostId",
            "OutpostArn",
            "HostRecovery",
            "AutoPlacement",
        ]

        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()

        for host in hosts_data:
            # Create a clean row with only the required fields
            row = {field: host.get(field, "") for field in fieldnames}
            writer.writerow(row)
