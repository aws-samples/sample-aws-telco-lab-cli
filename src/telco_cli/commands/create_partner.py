# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Create Partner Command implementation."""

import argparse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.services.account_provisioning import (
    AccountProvisioningEngine,
    AccountProvisioningRequest,
)
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger
from telco_cli.utils.validation import validate_aws_account_id, validate_partner_name

logger = get_logger(__name__)


class CreatePartnerCommand(BaseCommand):
    """Create a new partner account with cross-account assume role configuration."""

    @property
    def name(self) -> str:
        return "create-partner"

    @property
    def description(self) -> str:
        return "Create partner account with cross-account assume role configuration"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--partner-name",
            required=True,
            help="Unique identifier for the partner (e.g., nokia, cisco)",
        )
        parser.add_argument(
            "--partner-account-id",
            required=True,
            help="Partner-owned AWS account ID (12-digit number) that will be trusted",
        )
        parser.add_argument(
            "--admin-account-ids",
            required=True,
            help="Comma-separated list of AWS account IDs for JDA admin role trust policy",
        )
        parser.add_argument(
            "--validation-duration",
            default="30d",
            help="Duration for validation environment (default: 30d)",
        )
        parser.add_argument(
            "--account-type",
            choices=["joint-developer", "sandbox", "production"],
            default="joint-developer",
            help="Type of AWS account to create",
        )
        parser.add_argument(
            "--contact-email",
            help="Partner contact email address (optional, will auto-generate if not provided)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the create partner command."""
        try:
            logger.info(f"Creating partner account for: {args.partner_name}")

            # Validate inputs
            if not validate_partner_name(args.partner_name):
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    "Invalid partner name format. Must be 3-64 characters, start with letter, contain only letters, numbers, hyphens, underscores.",
                )

            if not validate_aws_account_id(args.partner_account_id):
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    "Partner account ID must be a 12-digit AWS account number",
                )

            # Create partner account
            result = self._create_partner_account(args)

            # Output result
            console.print_json(data=result)

        except TelcoCLIException:
            raise
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            raise TelcoCLIException(ErrorCode.USER_CANCELLED, "Operation cancelled by user")
        except Exception as e:
            logger.exception("Unexpected error during partner creation")
            raise TelcoCLIException(ErrorCode.PARTNER_CREATION_FAILED, str(e))

    def _parse_duration_to_days(self, duration_str: str) -> int:
        """Parse duration string to days."""
        try:
            if duration_str.endswith("d"):
                return int(duration_str[:-1])
            elif duration_str.endswith("h"):
                return max(1, int(duration_str[:-1]) // 24)
            elif duration_str.endswith("m"):
                return max(1, int(duration_str[:-1]) // (24 * 60))
            else:
                return int(duration_str)  # Assume days
        except (ValueError, TypeError):
            logger.error(f"Invalid duration format: {duration_str}")
            raise TelcoCLIException(
                ErrorCode.VALIDATION_ERROR, f"Invalid duration format: {duration_str}"
            )

    def _create_partner_account(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Create the partner account with AWS Organizations and IAM integration."""
        try:
            # Parse validation duration
            duration_days = self._parse_duration_to_days(args.validation_duration)

            # Parse admin account IDs
            admin_account_ids = [
                account_id.strip() for account_id in args.admin_account_ids.split(",")
            ]

            # Auto-generate contact email if not provided
            # NOTE: Replace with your organization's email format for production use
            partner_upper = args.partner_name.upper()
            contact_email = args.contact_email or f"admin+{partner_upper.lower()}@example.com"

            # Create account name
            # NOTE: Replace with your organization's naming convention for production use
            account_name = f"partner-{partner_upper.lower()}-account"

            console.print(f"🏗️ [bold cyan]Creating account for {args.partner_name}...[/bold cyan]")
            console.print(f"📧 Contact email: [blue]{contact_email}[/blue]")
            console.print(f"🏢 Account name: [yellow]{account_name}[/yellow]")
            console.print(
                f"🤝 Partner account ID to trust: [green]{args.partner_account_id}[/green]"
            )

            # Create provisioning request
            request = AccountProvisioningRequest(
                partner_name=args.partner_name,
                contact_email=contact_email,
                account_name=account_name,
                partner_account_id=args.partner_account_id,
                admin_account_ids=admin_account_ids,
                validation_duration_days=duration_days,
                account_type=args.account_type,
            )

            # Create provisioning engine and execute
            provisioning_engine = AccountProvisioningEngine()
            result = provisioning_engine.provision_partner_account(request)

            if result.success:
                # Create comprehensive response
                account_data = {
                    "Success": True,
                    "PartnerAccount": {
                        "PartnerName": args.partner_name,
                        "AccountId": result.aws_account_id,
                        "AccountName": result.account_name,
                        "ContactEmail": contact_email,
                        "AccountType": args.account_type,
                        "ValidationDurationDays": duration_days,
                        "Status": "ACTIVE",
                        "CreatedAt": datetime.now(timezone.utc).isoformat(),
                        "ExpiresAt": (
                            datetime.now(timezone.utc) + timedelta(days=duration_days)
                        ).isoformat(),
                    },
                    "IAMSetup": {
                        "PrimaryRoleArn": result.cross_account_role_arn,
                        "PrimaryRoleName": (result.role_result or {}).get(
                            "role_name", f"{partner_upper}-Admin"
                        ),
                        "AllRoles": (result.role_result or {}).get("roles_created", []),
                        "BoundaryPolicyArn": (result.role_result or {}).get("boundary_policy_arn"),
                        "TargetAccountId": (result.role_result or {}).get(
                            "target_account_id", result.aws_account_id
                        ),
                        "TrustedAccountId": args.partner_account_id,
                        "AdminAccountIds": admin_account_ids,
                        "SwitchRoleInstructions": "Use the switch_role_url from any role in AllRoles to access the account",
                    },
                    "ProvisioningTimeSeconds": result.provisioning_time_seconds,
                    "Message": f"Partner account '{args.partner_name}' created successfully",
                }

                return account_data
            else:
                raise TelcoCLIException(
                    ErrorCode.PARTNER_CREATION_FAILED, result.error_message or "Unknown error"
                )

        except TelcoCLIException:
            raise
        except Exception as e:
            logger.exception("Unexpected error during partner account creation")
            raise TelcoCLIException(ErrorCode.PARTNER_CREATION_FAILED, str(e))
