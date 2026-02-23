# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Get Outpost Utilization Summary Command implementation."""

import argparse
import json
import sys
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError
from rich.console import Console

from telco_cli.types.base_command import BaseCommand
from telco_cli.types.outpost_data import OutpostSummary
from telco_cli.utils.outpost_analyzer import OutpostAnalyzer
from telco_cli.utils.outpost_formatter import OutpostUtilizationFormatter


class GetOutpostUtilizationSummaryCommand(BaseCommand):
    """Get utilization summary across all Outposts."""

    def __init__(self):
        self.console = Console()
        self.analyzer = OutpostAnalyzer()
        self.formatter = OutpostUtilizationFormatter(self.console)

    @property
    def name(self) -> str:
        return "get-outpost-utilization-summary"

    @property
    def description(self) -> str:
        return "Get utilization summary across all Outposts"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--region-filter", help="Filter by specific region (e.g., us-west-2)")
        parser.add_argument(
            "--outpost-id", help="Show enhanced rack view for specific outpost (e.g., op-123456789)"
        )
        parser.add_argument(
            "--include-details", action="store_true", help="Include detailed per-Outpost breakdown"
        )
        parser.add_argument(
            "--output",
            choices=["json", "table", "summary"],
            default="json",
            help="Output format (default: json)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the get outpost utilization summary command."""
        try:
            result = self._get_utilization_summary(args)

            if args.output == "table":
                self._display_table_format(result)
            elif args.output == "summary":
                self.formatter.display_summary_format(result)
            else:
                print(json.dumps(result, indent=2))

        except Exception as e:
            error_result = {"Error": {"Code": "UtilizationSummaryError", "Message": str(e)}}
            print(json.dumps(error_result, indent=2), file=sys.stderr)
            sys.exit(1)

    def _get_utilization_summary(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Get comprehensive utilization summary across all Outposts."""
        try:
            outposts_client = boto3.client("outposts")
            ec2_client = boto3.client("ec2")

            # Get all Outposts
            outposts = self._fetch_outposts(outposts_client, args)

            # Get all dedicated hosts
            all_hosts = self._fetch_hosts(ec2_client)

            # Process each Outpost
            summaries = []
            for outpost in outposts:
                summary = self._create_outpost_summary(
                    outpost, all_hosts, outposts_client, ec2_client
                )
                summaries.append(summary)

            # Generate analysis
            regional_breakdown = self.analyzer.generate_regional_breakdown(summaries)

            # Calculate totals
            total_capacity = sum(s.assets.total for s in summaries)
            used_capacity = sum(s.instances.running for s in summaries)
            overall_utilization = (
                (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
            )

            return {
                "Success": True,
                "Summary": {
                    "total_outposts": len(summaries),
                    "total_capacity": total_capacity,
                    "used_capacity": used_capacity,
                    "overall_utilization": round(overall_utilization, 2),
                },
                "Outposts": [self._summary_to_dict(s) for s in summaries],
                "RegionalBreakdown": [self._regional_to_dict(r) for r in regional_breakdown],
            }

        except ClientError as e:
            return {"Success": False, "Error": str(e)}

    def _fetch_outposts(self, client, args) -> List[Dict[str, Any]]:
        """Fetch Outposts with filtering."""
        paginator = client.get_paginator("list_outposts")
        outposts = []

        for page in paginator.paginate():
            outposts.extend(page["Outposts"])

        # Apply filters
        if args.region_filter:
            outposts = [
                op for op in outposts if op["AvailabilityZone"].startswith(args.region_filter)
            ]

        if args.outpost_id:
            outposts = [op for op in outposts if op["OutpostId"] == args.outpost_id]

        return outposts

    def _fetch_hosts(self, ec2_client) -> List[Dict[str, Any]]:
        """Fetch all dedicated hosts."""
        paginator = ec2_client.get_paginator("describe_hosts")
        hosts = []

        for page in paginator.paginate():
            hosts.extend(page["Hosts"])

        return hosts

    def _create_outpost_summary(
        self, outpost, all_hosts, outposts_client, ec2_client
    ) -> OutpostSummary:
        """Create OutpostSummary from raw data."""
        outpost_id = outpost["OutpostId"]
        outpost_arn = outpost["OutpostArn"]

        # Filter hosts for this outpost
        outpost_hosts = [h for h in all_hosts if h.get("OutpostId") == outpost_id]

        # Analyze components
        assets = self.analyzer.analyze_outpost_assets(outpost_id, outposts_client)
        instances = self.analyzer.analyze_outpost_instances(outpost_arn, ec2_client)
        hosts_data = self.analyzer.analyze_outpost_hosts(outpost, outpost_hosts)

        return OutpostSummary(
            outpost_id=outpost_id,
            name=outpost.get("Name", ""),
            region=outpost["AvailabilityZone"][:-1],  # Remove AZ suffix
            availability_zone=outpost["AvailabilityZone"],
            state=outpost.get("LifeCycleStatus", ""),
            assets=assets,
            instances=instances,
            hosts_data=hosts_data,
        )

    def _display_table_format(self, result: Dict[str, Any]) -> None:
        """Display results in table format."""
        if not result.get("Success"):
            self.console.print(f"❌ [red]Error: {result.get('Error', 'Unknown error')}[/red]")
            return

        # Convert back to OutpostSummary objects for display
        summaries = [self._dict_to_summary(s) for s in result.get("Outposts", [])]
        regional_breakdown = [
            self._dict_to_regional(r) for r in result.get("RegionalBreakdown", [])
        ]

        self.formatter.display_summary_table(summaries)
        self.formatter.display_regional_breakdown(regional_breakdown)

    def _summary_to_dict(self, summary: OutpostSummary) -> Dict[str, Any]:
        """Convert OutpostSummary to dictionary."""
        return {
            "outpost_id": summary.outpost_id,
            "name": summary.name,
            "region": summary.region,
            "availability_zone": summary.availability_zone,
            "state": summary.state,
            "assets": {"total": summary.assets.total, "types": summary.assets.types},
            "instances": {
                "total": summary.instances.total,
                "running": summary.instances.running,
                "states": summary.instances.states,
            },
            "utilization_percentage": summary.utilization_percentage,
            "hosts_data": summary.hosts_data,
        }

    def _dict_to_summary(self, data: Dict[str, Any]) -> OutpostSummary:
        """Convert dictionary back to OutpostSummary."""
        from telco_cli.types.outpost_data import OutpostAssets, OutpostInstances

        assets_data = data.get("assets", {})
        instances_data = data.get("instances", {})

        return OutpostSummary(
            outpost_id=data["outpost_id"],
            name=data["name"],
            region=data["region"],
            availability_zone=data["availability_zone"],
            state=data["state"],
            assets=OutpostAssets(
                total=assets_data.get("total", 0), types=assets_data.get("types", {}), details=[]
            ),
            instances=OutpostInstances(
                total=instances_data.get("total", 0),
                running=instances_data.get("running", 0),
                states=instances_data.get("states", {}),
            ),
            hosts_data=data.get("hosts_data", {}),
        )

    def _regional_to_dict(self, regional) -> Dict[str, Any]:
        """Convert RegionalBreakdown to dictionary."""
        return {
            "region": regional.region,
            "outpost_count": regional.outpost_count,
            "total_capacity": regional.total_capacity,
            "used_capacity": regional.used_capacity,
            "utilization_percentage": regional.utilization_percentage,
        }

    def _dict_to_regional(self, data: Dict[str, Any]):
        """Convert dictionary back to RegionalBreakdown."""
        from telco_cli.types.outpost_data import RegionalBreakdown

        return RegionalBreakdown(
            region=data["region"],
            outpost_count=data["outpost_count"],
            total_capacity=data["total_capacity"],
            used_capacity=data["used_capacity"],
            utilization_percentage=data["utilization_percentage"],
        )
