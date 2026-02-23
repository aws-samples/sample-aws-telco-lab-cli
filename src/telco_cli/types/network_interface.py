# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Network interface data types."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class NetworkInterface:
    """Represents a network interface with its properties."""

    name: str
    status: str
    ip_address: Optional[str] = None
    speed: Optional[str] = None
    driver: Optional[str] = None
    sriov_capability: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Check if the interface is active."""
        return self.status == "ACTIVE"

    @property
    def has_sriov(self) -> bool:
        """Check if the interface supports SR-IOV."""
        return bool(self.sriov_capability and "Capable" in self.sriov_capability)
