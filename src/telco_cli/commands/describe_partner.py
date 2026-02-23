# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Describe Partner Command implementation."""

import argparse

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.services.account_provisioning import AccountProvisioningEngine
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger

logger = get_logger(__name__)


class DescribePartnerCommand(BaseCommand):
    """Describe a specific partner account."""

    @property
    def name(self) -> str:
        return "describe-partner"

    @property
    def description(self) -> str:
        return "Describe a specific partner account"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--partner-name", required=True, help="Name of the partner to describe")

    def run(self, args: argparse.Namespace) -> None:
        """Execute the describe partner command."""
        try:
            logger.info(f"Describing partner: {args.partner_name}")

            provisioning_engine = AccountProvisioningEngine()
            partner = provisioning_engine.get_partner_account(args.partner_name)

            if not partner:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR, f"Partner '{args.partner_name}' not found"
                )

            # Display partner details
            console.print_json(data=partner)

        except TelcoCLIException:
            raise
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error retrieving partner details: {e}")
            raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, str(e))
        except Exception as e:
            logger.exception("Failed to describe partner")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, str(e))
