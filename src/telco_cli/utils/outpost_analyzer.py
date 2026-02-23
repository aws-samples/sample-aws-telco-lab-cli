# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Outpost utilization analysis utilities."""

from typing import Any, Dict, List

from telco_cli.types.outpost_data import (
    InstanceTypeBreakdown,
    OutpostAssets,
    OutpostInstances,
    OutpostSummary,
    RegionalBreakdown,
)


class OutpostAnalyzer:
    """Analyzes Outpost utilization data."""

    @staticmethod
    def analyze_outpost_assets(outpost_id: str, outposts_client) -> OutpostAssets:
        """Analyze Outpost assets."""
        try:
            response = outposts_client.list_assets(OutpostIdentifier=outpost_id)
            assets = response.get("Assets", [])

            types: Dict[str, int] = {}
            for asset in assets:
                asset_type = asset.get("AssetType", "Unknown")
                types[asset_type] = types.get(asset_type, 0) + 1

            return OutpostAssets(total=len(assets), types=types, details=assets)
        except Exception:
            return OutpostAssets(total=0, types={}, details=[])

    @staticmethod
    def analyze_outpost_instances(outpost_arn: str, ec2_client) -> OutpostInstances:
        """Analyze Outpost instances."""
        try:
            response = ec2_client.describe_instances(
                Filters=[{"Name": "outpost-arn", "Values": [outpost_arn]}]
            )

            instances = []
            for reservation in response.get("Reservations", []):
                instances.extend(reservation.get("Instances", []))

            states: Dict[str, int] = {}
            running_count = 0

            for instance in instances:
                state = instance.get("State", {}).get("Name", "unknown")
                states[state] = states.get(state, 0) + 1
                if state == "running":
                    running_count += 1

            return OutpostInstances(total=len(instances), running=running_count, states=states)
        except Exception:
            return OutpostInstances(total=0, running=0, states={})

    @staticmethod
    def analyze_outpost_hosts(
        outpost: Dict[str, Any], hosts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze Outpost dedicated hosts."""
        if not hosts:
            return {"total": 0, "available": 0, "utilization": 0.0}

        available_hosts = sum(1 for host in hosts if host.get("State") == "available")
        total_hosts = len(hosts)
        utilization = (
            ((total_hosts - available_hosts) / total_hosts * 100) if total_hosts > 0 else 0
        )

        return {
            "total": total_hosts,
            "available": available_hosts,
            "utilization": round(utilization, 2),
        }

    @staticmethod
    def generate_regional_breakdown(summaries: List[OutpostSummary]) -> List[RegionalBreakdown]:
        """Generate regional utilization breakdown."""
        regional_data = {}

        for summary in summaries:
            region = summary.region
            if region not in regional_data:
                regional_data[region] = {
                    "outpost_count": 0,
                    "total_capacity": 0,
                    "used_capacity": 0,
                }

            regional_data[region]["outpost_count"] += 1
            regional_data[region]["total_capacity"] += summary.assets.total
            regional_data[region]["used_capacity"] += summary.instances.running

        breakdowns = []
        for region, data in regional_data.items():
            utilization = (
                (data["used_capacity"] / data["total_capacity"] * 100)
                if data["total_capacity"] > 0
                else 0
            )
            breakdowns.append(
                RegionalBreakdown(
                    region=region,
                    outpost_count=data["outpost_count"],
                    total_capacity=data["total_capacity"],
                    used_capacity=data["used_capacity"],
                    utilization_percentage=round(utilization, 2),
                )
            )

        return sorted(breakdowns, key=lambda x: x.region)

    @staticmethod
    def generate_instance_type_breakdown(
        summaries: List[OutpostSummary],
    ) -> List[InstanceTypeBreakdown]:
        """Generate instance type utilization breakdown."""
        total_instances = sum(summary.instances.total for summary in summaries)

        # Simplified breakdown - would need actual instance type data
        if total_instances > 0:
            return [
                InstanceTypeBreakdown(
                    instance_type="mixed", count=total_instances, percentage=100.0
                )
            ]

        return []
