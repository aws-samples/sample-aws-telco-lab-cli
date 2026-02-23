# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Network interface parsing utilities."""

from typing import Dict, List, Optional

from telco_cli.types.network_interface import NetworkInterface


class NetworkInterfaceParser:
    """Parser for network interface command output."""

    @staticmethod
    def parse_interface_output(output: str) -> List[NetworkInterface]:
        """Parse enhanced network interface command output."""
        if not output.strip():
            return []

        lines = output.strip().split("\n")
        interfaces = {}
        section = "basic"
        current_interface = None

        for line in lines:
            line = line.strip()

            if line == "---IP---":
                section = "ip"
                continue
            elif line == "---SRIOV---":
                section = "sriov"
                continue

            if section == "basic":
                interfaces.update(NetworkInterfaceParser._parse_basic_info(line))
            elif section == "ip":
                current_interface = NetworkInterfaceParser._parse_ip_info(
                    line, interfaces, current_interface
                )
            elif section == "sriov":
                current_interface = NetworkInterfaceParser._parse_sriov_info(
                    line, interfaces, current_interface
                )

        return [
            NetworkInterface(
                name=data["name"],
                status=data["status"],
                ip_address=data["ip"] if data["ip"] != "-" else None,
                speed=data["speed"] if data["speed"] != "-" else None,
                driver=data["driver"] if data["driver"] != "Unknown" else None,
                sriov_capability=data["sriov"] if data["sriov"] != "Unknown" else None,
            )
            for data in interfaces.values()
        ]

    @staticmethod
    def _parse_basic_info(line: str) -> Dict[str, Dict[str, str]]:
        """Parse basic interface information."""
        interfaces = {}
        if ":" in line:
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0].rstrip(":")
                status = "ACTIVE" if "UP" in parts[1] else "Inactive"
                interfaces[name] = {
                    "name": name,
                    "status": status,
                    "ip": "-",
                    "speed": "-",
                    "driver": "Unknown",
                    "sriov": "Unknown",
                }
        return interfaces

    @staticmethod
    def _parse_ip_info(
        line: str, interfaces: Dict[str, Dict[str, str]], current_interface: Optional[str]
    ) -> Optional[str]:
        """Parse IP address information."""
        if line and not line.startswith(" "):
            # New interface line
            parts = line.split(":")
            if len(parts) >= 2:
                current_interface = parts[1].strip().split()[0]
        elif "inet " in line and current_interface and current_interface in interfaces:
            # IP address line
            ip_match = line.split()
            if len(ip_match) >= 2:
                ip_addr = ip_match[1].split("/")[0]
                interfaces[current_interface]["ip"] = ip_addr
        return current_interface

    @staticmethod
    def _parse_sriov_info(
        line: str, interfaces: Dict[str, Dict[str, str]], current_interface: Optional[str]
    ) -> Optional[str]:
        """Parse SR-IOV and hardware information."""
        if line.startswith("Interface: "):
            current_interface = line.replace("Interface: ", "")
        elif current_interface and current_interface in interfaces:
            if line.startswith("SR-IOV: "):
                sriov_info = line.replace("SR-IOV: ", "")
                interfaces[current_interface]["sriov"] = sriov_info
            elif line.startswith("Driver: "):
                driver_info = line.replace("Driver: ", "")
                interfaces[current_interface]["driver"] = driver_info
            elif line.startswith("Speed: "):
                speed_info = line.replace("Speed: ", "")
                interfaces[current_interface]["speed"] = speed_info
        return current_interface
