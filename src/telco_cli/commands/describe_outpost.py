# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Describe Outpost Command implementation."""

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from telco_cli.types.base_command import BaseCommand


class DescribeOutpostCommand(BaseCommand):
    """Get detailed information about a specific Outpost."""

    def __init__(self):
        self.console = Console()

    @property
    def name(self) -> str:
        return "describe-outpost"

    @property
    def description(self) -> str:
        return "Get detailed information about a specific Outpost"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--outpost-id", required=True, help="Outpost ID to describe")
        parser.add_argument(
            "--include-capacity",
            action="store_true",
            help="Include detailed capacity and instance type information",
        )
        parser.add_argument(
            "--include-hosts", action="store_true", help="Include dedicated hosts information"
        )
        parser.add_argument(
            "--include-instances", action="store_true", help="Include running instances information"
        )
        parser.add_argument(
            "--output",
            choices=["json", "table", "summary"],
            default="json",
            help="Output format (default: json)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the describe outpost command."""
        try:
            result = self._describe_outpost(args)

            if args.output == "table":
                self._print_table_format(result)
            elif args.output == "summary":
                self._print_summary_format(result)
            else:
                print(json.dumps(result, indent=2))

        except Exception as e:
            if args.output in ["table", "summary"]:
                self.console.print(f"❌ Error: {str(e)}", style="bold red")
            else:
                error_result = {"Error": {"Code": "OutpostDescribeError", "Message": str(e)}}
                print(json.dumps(error_result, indent=2), file=sys.stderr)
            sys.exit(1)

    def _describe_outpost(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Get detailed information about the specified Outpost."""
        try:
            outposts_client = boto3.client("outposts")

            # Get Outpost details
            try:
                response = outposts_client.get_outpost(OutpostId=args.outpost_id)
                outpost = response["Outpost"]
            except ClientError as e:
                if e.response["Error"]["Code"] == "NotFoundException":
                    return {
                        "Success": False,
                        "Error": {
                            "Code": "OutpostNotFound",
                            "Message": f"Outpost {args.outpost_id} not found",
                        },
                    }
                else:
                    raise

            # Build basic outpost information
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

            # Get site information
            try:
                site_response = outposts_client.get_site(SiteId=outpost["SiteId"])
                site = site_response["Site"]
                outpost_info["SiteDetails"] = {
                    "Name": site.get("Name", "Unnamed"),
                    "Description": site.get("Description", ""),
                    "Country": site.get("Country", "Unknown"),
                    "State": site.get("State", "Unknown"),
                    "City": site.get("City", "Unknown"),
                    "Address": site.get("Address", {}),
                    "Tags": {tag["Key"]: tag["Value"] for tag in site.get("Tags", [])},
                }
            except Exception as e:
                outpost_info["SiteDetails"] = {
                    "Error": f"Could not retrieve site details: {str(e)}"
                }

            # Get capacity information if requested
            if args.include_capacity:
                capacity_info = self._get_outpost_capacity_details(outposts_client, args.outpost_id)
                outpost_info["CapacityDetails"] = capacity_info

            # Get dedicated hosts information if requested
            if args.include_hosts:
                hosts_info = self._get_outpost_hosts_details(outposts_client, args.outpost_id)
                outpost_info["PhysicalAssets"] = hosts_info

            # Get instances information if requested
            if args.include_instances:
                instances_info = self._get_outpost_instances_details(args.outpost_id)
                outpost_info["InstancesDetails"] = instances_info

            return {
                "Success": True,
                "Outpost": outpost_info,
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

    def _get_outpost_capacity_details(self, outposts_client, outpost_id: str) -> Dict[str, Any]:
        """Get detailed capacity information for the Outpost."""
        try:
            # Get supported instance types
            response = outposts_client.get_outpost_instance_types(OutpostId=outpost_id)
            instance_types = response.get("InstanceTypes", [])

            # Categorize instance types
            compute_optimized = []
            memory_optimized = []
            storage_optimized = []
            general_purpose = []
            accelerated_computing = []

            for it in instance_types:
                instance_type = it["InstanceType"]
                if instance_type.startswith("c"):
                    compute_optimized.append(instance_type)
                elif instance_type.startswith("r") or instance_type.startswith("x"):
                    memory_optimized.append(instance_type)
                elif instance_type.startswith("d") or instance_type.startswith("i"):
                    storage_optimized.append(instance_type)
                elif instance_type.startswith("m") or instance_type.startswith("t"):
                    general_purpose.append(instance_type)
                elif instance_type.startswith("p") or instance_type.startswith("g"):
                    accelerated_computing.append(instance_type)
                else:
                    general_purpose.append(instance_type)

            return {
                "TotalInstanceTypes": len(instance_types),
                "ByCategory": {
                    "ComputeOptimized": sorted(compute_optimized),
                    "MemoryOptimized": sorted(memory_optimized),
                    "StorageOptimized": sorted(storage_optimized),
                    "GeneralPurpose": sorted(general_purpose),
                    "AcceleratedComputing": sorted(accelerated_computing),
                },
                "AllInstanceTypes": sorted([it["InstanceType"] for it in instance_types]),
                "RawDetails": instance_types,
            }

        except Exception as e:
            return {"Error": f"Could not retrieve capacity details: {str(e)}"}

    def _get_outpost_hosts_details(self, outposts_client: Any, outpost_id: str) -> Dict[str, Any]:
        """Get physical assets information using AWS outposts list-assets."""
        try:
            response = outposts_client.list_assets(OutpostIdentifier=outpost_id)
            assets = response.get("Assets", [])

            # Filter for compute assets
            compute_assets = [asset for asset in assets if asset.get("AssetType") == "COMPUTE"]

            if not compute_assets:
                return {"TotalAssets": 0, "Message": "No compute assets found for this Outpost"}

            # vCPU mapping for instance families (since MaxVcpus might not be in API response)
            vcpu_mapping = {
                "R7izde": 128,  # R7izde instances have 128 vCPUs
                "Bmn-sf2": 128,  # Bmn-sf2.metal-32xl has 128 vCPUs
                "Bmn-cx2": 192,  # Bmn-cx2.metal-48xl has 192 vCPUs
            }

            # Process assets
            asset_details = []
            by_state: Dict[str, int] = {}
            by_instance_family: Dict[str, int] = {}
            by_rack: Dict[str, int] = {}
            total_vcpus = 0
            available_vcpus = 0

            for asset in compute_assets:
                compute_attrs = asset.get("ComputeAttributes", {})
                asset_location = asset.get("AssetLocation", {})

                # Count by state
                state = compute_attrs.get("State", "Unknown")
                by_state[state] = by_state.get(state, 0) + 1

                # Count by instance family
                families = compute_attrs.get("InstanceFamilies", [])
                for family in families:
                    by_instance_family[family] = by_instance_family.get(family, 0) + 1

                # Count by rack
                rack_id = asset.get("RackId", "Unknown")
                by_rack[rack_id] = by_rack.get(rack_id, 0) + 1

                # Calculate vCPUs - use MaxVcpus if available, otherwise map from instance family
                max_vcpus = compute_attrs.get("MaxVcpus", 0)
                if max_vcpus == 0 and families:
                    # Fallback to mapping if MaxVcpus not available
                    max_vcpus = vcpu_mapping.get(families[0], 0)

                if state == "ACTIVE":
                    total_vcpus += max_vcpus
                    # Available vCPUs = total minus dedicated host allocations
                    if not compute_attrs.get("HostId"):
                        available_vcpus += max_vcpus

                # Enhanced asset detail with capacity information
                instance_capacities = compute_attrs.get("InstanceTypeCapacities", [])
                capacity_info = []
                for cap in instance_capacities:
                    capacity_info.append(
                        {"InstanceType": cap.get("InstanceType"), "Count": cap.get("Count", 0)}
                    )

                asset_detail = {
                    "AssetId": asset.get("AssetId"),
                    "RackId": rack_id,
                    "AssetType": asset.get("AssetType"),
                    "HostId": compute_attrs.get("HostId"),
                    "State": state,
                    "InstanceFamilies": families,
                    "MaxVcpus": max_vcpus,
                    "RackElevation": asset_location.get("RackElevation"),
                    "InstanceTypeCapacities": capacity_info,
                    "IsDedicatedHost": bool(compute_attrs.get("HostId")),
                }
                asset_details.append(asset_detail)

            return {
                "TotalAssets": len(compute_assets),
                "TotalVcpus": total_vcpus,
                "AvailableVcpus": available_vcpus,
                "ByState": by_state,
                "ByInstanceFamily": by_instance_family,
                "ByRack": by_rack,
                "AssetDetails": asset_details,
            }

        except Exception as e:
            return {"Error": f"Could not retrieve physical assets: {str(e)}"}

    def _get_outpost_instances_details(self, outpost_id: str) -> Dict[str, Any]:
        """Get detailed instances information using AWS outposts list-asset-instances."""
        try:
            # Use AWS CLI subprocess call since boto3 version doesn't support list_asset_instances
            import json
            import os
            import subprocess

            # Build AWS CLI command
            cmd = [
                "aws",
                "outposts",
                "list-asset-instances",
                "--outpost-identifier",
                outpost_id,
                "--output",
                "json",
            ]

            # Add profile and region from environment if available
            aws_profile = os.environ.get("AWS_PROFILE")
            if aws_profile:
                cmd.extend(["--profile", aws_profile])
            aws_region = os.environ.get("AWS_DEFAULT_REGION")
            if aws_region:
                cmd.extend(["--region", aws_region])

            # Execute AWS CLI command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {"Error": f"AWS CLI error: {result.stderr.strip()}"}

            # Parse JSON response
            response = json.loads(result.stdout)
            asset_instances = response.get("AssetInstances", [])

            # Group by instance type and account
            by_instance_type = {}
            by_account = {}

            for instance in asset_instances:
                instance_type = instance.get("InstanceType", "Unknown")
                account_id = instance.get("AccountId", instance.get("AwsServiceName", "Unknown"))

                # Count by instance type
                if instance_type not in by_instance_type:
                    by_instance_type[instance_type] = 0
                by_instance_type[instance_type] += 1

                # Count by account
                if account_id not in by_account:
                    by_account[account_id] = 0
                by_account[account_id] += 1

            return {
                "TotalInstances": len(asset_instances),
                "ByInstanceType": by_instance_type,
                "ByAccount": by_account,
                "InstanceDetails": [
                    {
                        "InstanceId": instance.get("InstanceId", "Unknown"),
                        "InstanceType": instance.get("InstanceType", "Unknown"),
                        "AssetId": instance.get("AssetId", "Unknown"),
                        "AccountId": instance.get(
                            "AccountId", instance.get("AwsServiceName", "Unknown")
                        ),
                    }
                    for instance in asset_instances
                ],
            }

        except Exception as e:
            return {"Error": f"Could not retrieve instances details: {str(e)}"}

    def _get_outpost_physical_assets(self, outpost_id: str) -> Dict[str, Any]:
        """Get physical assets (servers) information using AWS outposts list-assets."""
        try:
            outposts_client = boto3.client("outposts")
            response = outposts_client.list_assets(OutpostIdentifier=outpost_id)

            assets = response.get("Assets", [])
            compute_assets = [asset for asset in assets if asset.get("AssetType") == "COMPUTE"]

            # Count by state and instance family
            by_state = {}
            by_instance_family = {}
            total_vcpus = 0

            asset_details = []
            for asset in compute_assets:
                compute_attrs = asset.get("ComputeAttributes", {})
                state = compute_attrs.get("State", "Unknown")
                instance_families = compute_attrs.get("InstanceFamilies", [])
                max_vcpus = compute_attrs.get("MaxVcpus", 0)
                host_id = compute_attrs.get("HostId")

                # Count by state
                if state not in by_state:
                    by_state[state] = 0
                by_state[state] += 1

                # Count by instance family
                for family in instance_families:
                    if family not in by_instance_family:
                        by_instance_family[family] = 0
                    by_instance_family[family] += 1

                total_vcpus += max_vcpus

                asset_details.append(
                    {
                        "AssetId": asset.get("AssetId", "Unknown"),
                        "State": state,
                        "InstanceFamilies": instance_families,
                        "MaxVcpus": max_vcpus,
                        "HostId": host_id,
                        "RackElevation": asset.get("AssetLocation", {}).get("RackElevation"),
                        "InstanceTypeCapacities": compute_attrs.get("InstanceTypeCapacities", []),
                    }
                )

            return {
                "TotalAssets": len(compute_assets),
                "ByState": by_state,
                "ByInstanceFamily": by_instance_family,
                "TotalVcpus": total_vcpus,
                "AssetDetails": asset_details,
            }

        except Exception as e:
            return {"Error": f"Could not retrieve assets details: {str(e)}"}

    def _safe_get_capacity(self, capacity) -> int:
        """Safely extract capacity value."""
        if isinstance(capacity, int):
            return capacity
        elif isinstance(capacity, dict):
            # Filter out non-numeric values before summing
            numeric_values = [v for v in capacity.values() if isinstance(v, (int, float))]
            return round(sum(numeric_values)) if numeric_values else 0
        else:
            return 0

    def _print_table_format(self, result: Dict[str, Any]) -> None:
        """Print results in table format using rich."""
        if not result.get("Success", True):
            self.console.print(
                f"❌ Error: {result.get('Error', {}).get('Message', 'Unknown error')}",
                style="bold red",
            )
            return

        outpost = result.get("Outpost", {})

        # Main outpost information panel
        info_text = f"""🏢 [bold cyan]{outpost.get('Name', 'Unnamed')}[/bold cyan]
📍 ID: [yellow]{outpost.get('OutpostId', 'Unknown')}[/yellow]
🌍 Site: [blue]{outpost.get('SiteDetails', {}).get('Name', 'Unknown')}[/blue]
📍 AZ: [green]{outpost.get('AvailabilityZone', 'Unknown')}[/green]
📊 Status: [{'green' if outpost.get('LifeCycleStatus') == 'ACTIVE' else 'yellow'}]{outpost.get('LifeCycleStatus', 'Unknown')}[/{'green' if outpost.get('LifeCycleStatus') == 'ACTIVE' else 'yellow'}]
🏗️ Type: [magenta]{outpost.get('SupportedHardwareType', 'Unknown')}[/magenta]"""

        self.console.print(Panel(info_text, title="🏢 Outpost Details", border_style="blue"))

        # Capacity information if available
        capacity = outpost.get("CapacityDetails")
        if capacity and not capacity.get("Error"):
            self.console.print("\n💾 [bold]Capacity Information:[/bold]")

            # Show supported instance types
            if capacity.get("AllInstanceTypes"):
                capacity_table = Table(title="Supported Instance Types")
                capacity_table.add_column("Instance Type", style="cyan", no_wrap=True)
                capacity_table.add_column("Category", style="magenta")

                # Add supported instance types
                for instance_type in capacity.get("AllInstanceTypes", []):
                    # Determine category
                    category = "Unknown"
                    for cat, types in capacity.get("ByCategory", {}).items():
                        if instance_type in types:
                            category = cat.replace("Optimized", "").replace("Computing", "")
                            break

                    capacity_table.add_row(instance_type, category)

                self.console.print(capacity_table)
                self.console.print(
                    f"\n📊 Total Supported Instance Types: [bold yellow]{capacity.get('TotalInstanceTypes', 0)}[/bold yellow]"
                )
            else:
                self.console.print("📭 [yellow]No capacity information available[/yellow]")

        # Physical assets information if available
        assets = outpost.get("PhysicalAssets")
        if assets and not assets.get("Error"):
            self.console.print(
                f"\n🖥️ [bold]Physical Assets ({assets.get('TotalAssets', 0)} total):[/bold]"
            )

            if assets.get("TotalAssets", 0) > 0:
                # Summary stats
                by_state = assets.get("ByState", {})
                if by_state:
                    state_summary = " | ".join(
                        [
                            f"[{'green' if state == 'ACTIVE' else 'yellow'}]{state}[/{'green' if state == 'ACTIVE' else 'yellow'}]: {count}"
                            for state, count in by_state.items()
                        ]
                    )
                    self.console.print(f"📊 By State: {state_summary}")

                by_family = assets.get("ByInstanceFamily", {})
                if by_family:
                    family_summary = " | ".join(
                        [f"[blue]{family}[/blue]: {count}" for family, count in by_family.items()]
                    )
                    self.console.print(f"🏗️ By Family: {family_summary}")

                # Asset details table
                asset_details = assets.get("AssetDetails", [])
                if asset_details:
                    asset_table = Table(title="Physical Asset Details")
                    asset_table.add_column("Asset ID", style="cyan", no_wrap=True)
                    asset_table.add_column("Host ID", style="magenta")
                    asset_table.add_column("State", style="green")
                    asset_table.add_column("Rack Elevation", justify="right", style="yellow")
                    asset_table.add_column("Instance Families", style="blue")

                    for asset in asset_details:
                        families_str = ", ".join(asset.get("InstanceFamilies", []))
                        elevation = asset.get("RackElevation")
                        elevation_str = f"{elevation}" if elevation is not None else "N/A"

                        asset_table.add_row(
                            asset.get("AssetId", "N/A"),
                            asset.get("HostId", "N/A"),
                            asset.get("State", "Unknown"),
                            elevation_str,
                            families_str,
                        )

                    self.console.print(asset_table)
            else:
                self.console.print("📭 No physical assets found for this Outpost")
            self.console.print(
                f"\n🖥️ [bold]Physical Assets ({assets.get('TotalAssets', 0)} total):[/bold]"
            )

            if assets.get("TotalAssets", 0) > 0:
                # Summary stats
                by_state = assets.get("ByState", {})
                if by_state:
                    state_summary = " | ".join(
                        [
                            (
                                f"{state}: [green]{count}[/green]"
                                if state == "ACTIVE"
                                else f"{state}: [red]{count}[/red]"
                            )
                            for state, count in by_state.items()
                        ]
                    )
                    self.console.print(f"📊 By State: {state_summary}")

                by_family = assets.get("ByInstanceFamily", {})
                if by_family:
                    family_summary = " | ".join(
                        [f"{family}: [cyan]{count}[/cyan]" for family, count in by_family.items()]
                    )
                    self.console.print(f"🏗️ By Family: {family_summary}")

                # Enhanced vCPU display
                total_vcpus = assets.get("TotalVcpus", 0)
                available_vcpus = assets.get("AvailableVcpus", 0)
                self.console.print(
                    f"💾 Total VCPUs: [bold yellow]{total_vcpus}[/bold yellow] ([green]{available_vcpus} available[/green])"
                )

                # Rack information
                by_rack = assets.get("ByRack", {})
                if by_rack and len(by_rack) > 1:
                    rack_summary = " | ".join(
                        [f"Rack {rack}: [blue]{count}[/blue]" for rack, count in by_rack.items()]
                    )
                    self.console.print(f"🏗️ By Rack: {rack_summary}")

                # Enhanced Assets table with rack information
                assets_table = Table(title="Physical Assets Details")
                assets_table.add_column("Asset ID", style="cyan", no_wrap=True)
                assets_table.add_column("Rack ID", style="blue", no_wrap=True)
                assets_table.add_column("State", style="green")
                assets_table.add_column("Instance Family", style="magenta")
                assets_table.add_column("VCPUs", justify="right", style="yellow")
                assets_table.add_column("Rack Position", justify="right", style="green")
                assets_table.add_column("Host ID", style="red")
                assets_table.add_column("Capacity", style="white")

                for asset in assets.get("AssetDetails", []):
                    state = asset.get("State", "Unknown")
                    if state == "ACTIVE":
                        state_display = f"[green]{state}[/green]"
                    elif state == "ISOLATED":
                        state_display = f"[red]{state}[/red]"
                    else:
                        state_display = f"[yellow]{state}[/yellow]"

                    families = ", ".join(asset.get("InstanceFamilies", []))
                    rack_pos = asset.get("RackElevation")
                    rack_display = f"{rack_pos}" if rack_pos else "N/A"
                    host_id = asset.get("HostId", "")
                    rack_id = asset.get("RackId", "Unknown")

                    # Enhanced capacity display
                    capacities = asset.get("InstanceTypeCapacities", [])
                    if capacities:
                        capacity_str = ", ".join(
                            [f"{cap['InstanceType']}x{cap['Count']}" for cap in capacities]
                        )
                    elif asset.get("IsDedicatedHost"):
                        capacity_str = "Dedicated Host"
                    else:
                        capacity_str = "Available"

                    assets_table.add_row(
                        asset.get("AssetId", "Unknown"),
                        rack_id,
                        state_display,
                        families or "Unknown",
                        str(asset.get("MaxVcpus", 0)),
                        rack_display,
                        host_id or "",
                        capacity_str,
                    )

                self.console.print(assets_table)
            else:
                self.console.print("📭 [yellow]No physical assets found for this Outpost[/yellow]")

        # Instances information if available
        instances = outpost.get("InstancesDetails")
        if instances and not instances.get("Error"):
            self.console.print(
                f"\n🚀 [bold]Running Instances ({instances.get('TotalInstances', 0)} total):[/bold]"
            )

            if instances.get("TotalInstances", 0) > 0:
                # Summary by instance type
                by_type = instances.get("ByInstanceType", {})
                if by_type:
                    type_summary = " | ".join(
                        [f"{itype}: [cyan]{count}[/cyan]" for itype, count in by_type.items()]
                    )
                    self.console.print(f"📊 By Type: {type_summary}")

                # Summary by account
                by_account = instances.get("ByAccount", {})
                if by_account:
                    account_summary = " | ".join(
                        [f"{acc}: [yellow]{count}[/yellow]" for acc, count in by_account.items()]
                    )
                    self.console.print(f"🏢 By Account: {account_summary}")

                # Instances table
                instances_table = Table(title="Instance Details")
                instances_table.add_column("Instance ID", style="cyan", no_wrap=True)
                instances_table.add_column("Instance Type", style="magenta")
                instances_table.add_column("Asset ID", style="blue")
                instances_table.add_column("Account ID", style="yellow")

                for instance in instances.get("InstanceDetails", []):
                    instances_table.add_row(
                        instance.get("InstanceId", "Unknown"),
                        instance.get("InstanceType", "Unknown"),
                        instance.get("AssetId", "Unknown"),
                        instance.get("AccountId", "Unknown"),
                    )

                self.console.print(instances_table)
            else:
                self.console.print("📭 [yellow]No instances found for this Outpost[/yellow]")

    def _print_summary_format(self, result: Dict[str, Any]) -> None:
        """Print results in summary format using rich."""
        if not result.get("Success", True):
            self.console.print(
                f"❌ Error: {result.get('Error', {}).get('Message', 'Unknown error')}",
                style="bold red",
            )
            return

        outpost = result.get("Outpost", {})

        self.console.print(
            f"🏢 [bold cyan]{outpost.get('Name', 'Unnamed')}[/bold cyan] ({outpost.get('OutpostId', 'Unknown')})"
        )
        self.console.print("=" * 50)
        self.console.print(
            f"📍 Site: [blue]{outpost.get('SiteDetails', {}).get('Name', 'Unknown')}[/blue]"
        )
        self.console.print(
            f"🌍 Availability Zone: [green]{outpost.get('AvailabilityZone', 'Unknown')}[/green]"
        )
        self.console.print(
            f"📊 Status: [{'green' if outpost.get('LifeCycleStatus') == 'ACTIVE' else 'yellow'}]{outpost.get('LifeCycleStatus', 'Unknown')}[/{'green' if outpost.get('LifeCycleStatus') == 'ACTIVE' else 'yellow'}]"
        )
        self.console.print(
            f"🏗️ Hardware Type: [magenta]{outpost.get('SupportedHardwareType', 'Unknown')}[/magenta]"
        )

        # Quick stats
        hosts = outpost.get("DedicatedHosts")
        if hosts and not hosts.get("Error") and hosts.get("TotalHosts", 0) > 0:
            self.console.print("\n🖥️ [bold]Dedicated Hosts:[/bold]")
            self.console.print(f"  Total: {hosts.get('TotalHosts', 0)}")
            self.console.print(f"  Available: [green]{hosts.get('AvailableHosts', 0)}[/green]")
            self.console.print(f"  Assigned: [yellow]{hosts.get('AssignedHosts', 0)}[/yellow]")

            util = hosts.get("UtilizationPercent", 0)
            if util >= 80:
                util_color = "red"
            elif util >= 60:
                util_color = "yellow"
            else:
                util_color = "green"
            self.console.print(f"  Utilization: [{util_color}]{util}%[/{util_color}]")

            # Instance type breakdown
            by_type = hosts.get("ByInstanceType", {})
            if by_type:
                self.console.print("\n📋 [bold]By Instance Type:[/bold]")
                for instance_type, counts in by_type.items():
                    self.console.print(
                        f"  [cyan]{instance_type}[/cyan]: {counts['total']} total ([green]{counts['available']} available[/green], [yellow]{counts['assigned']} assigned[/yellow])"
                    )

        capacity = outpost.get("CapacityDetails")
        if capacity and not capacity.get("Error"):
            self.console.print("\n💾 [bold]Capacity Available[/bold]")
            for instance_type, details in capacity.get("ByInstanceType", {}).items():
                available = details.get("AvailableCapacity", 0)
                total = details.get("TotalCapacity", 0)
                self.console.print(
                    f"  [cyan]{instance_type}[/cyan]: [green]{available}[/green] of {total} capacity units"
                )
