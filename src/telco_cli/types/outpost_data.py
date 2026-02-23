# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Outpost data types for utilization analysis."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class OutpostAssets:
    """Represents Outpost asset information."""

    total: int
    types: Dict[str, int]
    details: List[Dict[str, Any]]


@dataclass
class OutpostInstances:
    """Represents Outpost instance information."""

    total: int
    running: int
    states: Dict[str, int]


@dataclass
class OutpostSummary:
    """Represents comprehensive Outpost utilization data."""

    outpost_id: str
    name: str
    region: str
    availability_zone: str
    state: str
    assets: OutpostAssets
    instances: OutpostInstances
    hosts_data: Dict[str, Any]

    @property
    def utilization_percentage(self) -> float:
        """Calculate utilization percentage."""
        if self.assets.total == 0:
            return 0.0
        return (self.instances.running / self.assets.total) * 100


@dataclass
class RegionalBreakdown:
    """Represents regional utilization breakdown."""

    region: str
    outpost_count: int
    total_capacity: int
    used_capacity: int
    utilization_percentage: float


@dataclass
class InstanceTypeBreakdown:
    """Represents instance type utilization breakdown."""

    instance_type: str
    count: int
    percentage: float
