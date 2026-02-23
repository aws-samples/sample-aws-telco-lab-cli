# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Provisioning types and dataclasses."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AccountProvisioningRequest:
    """Request object for partner account provisioning."""

    partner_name: str
    contact_email: str
    account_name: str
    partner_account_id: str
    admin_account_ids: List[str]
    validation_duration_days: int
    account_type: str
    organizational_unit: Optional[str] = None


@dataclass
class AccountProvisioningResult:
    """Result object for partner account provisioning."""

    success: bool
    aws_account_id: Optional[str] = None
    account_name: Optional[str] = None
    cross_account_role_arn: Optional[str] = None
    error_message: Optional[str] = None
    provisioning_time_seconds: Optional[float] = None
    role_result: Optional[Dict[str, Any]] = None
