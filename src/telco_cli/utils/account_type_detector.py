# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Account type detection utilities for AWS Organizations."""

from typing import Any, Dict

from telco_cli.utils.account_constants import (
    ACCOUNT_TYPE_LEGACY,
    ACCOUNT_TYPE_MANAGEMENT,
    ACCOUNT_TYPE_PARTNER,
    ACCOUNT_TYPE_SECURITY,
    LEGACY_KEYWORDS,
    MANAGEMENT_KEYWORDS,
    PARTNER_KEYWORDS,
    PARTNER_TAGS,
    SECURITY_KEYWORDS,
)


class AccountTypeDetector:
    """Utility class for detecting AWS account types based on name and tags."""

    @staticmethod
    def determine_account_type(account: Dict[str, Any], tags: Dict[str, str]) -> str:
        """Determine the type of account based on name and tags."""
        account_name = account["Name"].lower()

        if AccountTypeDetector._is_management_account(account_name, tags):
            return ACCOUNT_TYPE_MANAGEMENT

        if AccountTypeDetector._is_security_account(account_name, tags):
            return ACCOUNT_TYPE_SECURITY

        if AccountTypeDetector._is_partner_account(account_name, tags):
            return ACCOUNT_TYPE_PARTNER

        if AccountTypeDetector._is_legacy_account(account_name, tags):
            return ACCOUNT_TYPE_LEGACY

        return ACCOUNT_TYPE_LEGACY

    @staticmethod
    def _is_management_account(account_name: str, tags: Dict[str, str]) -> bool:
        """Check if account is a management account."""
        if tags.get("AccountType") == ACCOUNT_TYPE_MANAGEMENT:
            return True

        return any(keyword in account_name for keyword in MANAGEMENT_KEYWORDS)

    @staticmethod
    def _is_security_account(account_name: str, tags: Dict[str, str]) -> bool:
        """Check if account is a security account."""
        if account_name in SECURITY_KEYWORDS:
            return True

        return any(keyword in account_name for keyword in SECURITY_KEYWORDS)

    @staticmethod
    def _is_partner_account(account_name: str, tags: Dict[str, str]) -> bool:
        """Check if account is a partner account."""
        managed_by_values = PARTNER_TAGS.get("ManagedBy")
        if managed_by_values is not None:
            managed_by_tag = tags.get("ManagedBy")
            if managed_by_tag and managed_by_tag in managed_by_values:
                return True

        if "Partner" in tags and tags["Partner"] is not None:
            return True

        return any(keyword in account_name for keyword in PARTNER_KEYWORDS)

    @staticmethod
    def _is_legacy_account(account_name: str, tags: Dict[str, str]) -> bool:
        """Check if account is a legacy account."""
        for keyword in LEGACY_KEYWORDS:
            if keyword.endswith("-"):
                if account_name.startswith(keyword):
                    return True
            else:
                if keyword in account_name:
                    return True

        return False
