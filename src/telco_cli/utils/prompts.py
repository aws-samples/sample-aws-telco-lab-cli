# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Shared prompt utilities for TelcoCLI commands."""

from typing import List, Optional

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.utils import console


def confirm_destructive_operation(
    operation_name: str,
    resource_name: str,
    details: Optional[List[str]] = None,
    skip_confirmation: bool = False,
    raise_on_cancel: bool = False,
) -> bool:
    """
    Confirm a destructive operation with the user.

    Args:
        operation_name: The action being performed (e.g., "delete", "revoke", "release")
        resource_name: The resource being acted upon (e.g., "partner 'Acme Corp'", "certificate")
        details: Optional list of detail lines to display
        skip_confirmation: If True, skip the confirmation prompt
        raise_on_cancel: If True, raise exception on cancel; if False, return False

    Returns:
        True if confirmed, False if cancelled (when raise_on_cancel=False)

    Raises:
        TelcoCLIException: If user cancels and raise_on_cancel=True
    """
    if skip_confirmation:
        return True

    # Print warning message (common for all cases)
    console.print(
        f"\n[bold yellow]Warning: This will {operation_name} {resource_name}[/bold yellow]"
    )

    # Print details if provided
    if details:
        for detail in details:
            console.print(f"   {detail}")

    # Get user confirmation
    response = input(f"\nAre you sure you want to {operation_name} {resource_name}? (yes/no): ")

    if response.lower() == "yes":
        return True

    console.print("[yellow]Operation cancelled.[/yellow]")

    if raise_on_cancel:
        raise TelcoCLIException(ErrorCode.USER_CANCELLED, "Operation cancelled by user")

    return False
