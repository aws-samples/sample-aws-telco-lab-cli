# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Delete Partner Command implementation."""

import argparse

import boto3
from botocore.exceptions import ClientError

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger
from telco_cli.utils.prompts import confirm_destructive_operation

logger = get_logger(__name__)


class DeletePartnerCommand(BaseCommand):
    """Delete a partner account."""

    @property
    def name(self) -> str:
        return "delete-partner"

    @property
    def description(self) -> str:
        return "Delete a partner account"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--partner-name", required=True, help="Name of the partner to delete")
        parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
        parser.add_argument(
            "--account-id",
            help="Specific account ID to delete (optional, will search by name if not provided)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the delete partner command."""
        try:
            logger.info(f"Deleting partner: {args.partner_name}")

            if not confirm_destructive_operation(
                operation_name="delete",
                resource_name=f"partner '{args.partner_name}'",
                skip_confirmation=args.force,
                raise_on_cancel=False,
            ):
                return

            # Implementation from commit d8f9925: Real AWS Organizations API
            result = self._delete_partner_real(args)

            if result.get("Success"):
                console.print(
                    f"[bold green]Partner '{args.partner_name}' deleted successfully[/bold green]"
                )
                console.print_json(data=result)
            else:
                raise TelcoCLIException(
                    ErrorCode.PARTNER_CREATION_FAILED,
                    result.get("Error", {}).get(
                        "Message", f"Failed to delete partner '{args.partner_name}'"
                    ),
                )

        except TelcoCLIException:
            raise
        except Exception as e:
            logger.exception("Failed to delete partner")
            raise TelcoCLIException(ErrorCode.PARTNER_LISTING_FAILED, str(e))

    def _delete_partner_real(self, args: argparse.Namespace) -> dict:
        """Delete the partner account using real AWS Organizations API (from commit d8f9925)."""
        try:
            org_client = boto3.client("organizations")

            # If account ID is provided, use it directly
            if args.account_id:
                account_id = args.account_id
                # Verify the account exists and get its details
                try:
                    account_response = org_client.describe_account(AccountId=account_id)
                    partner_account = account_response["Account"]
                except ClientError as e:
                    if e.response["Error"]["Code"] == "AccountNotFoundException":
                        raise TelcoCLIException(
                            ErrorCode.VALIDATION_ERROR, f"Account ID '{account_id}' not found"
                        )
                    raise
            else:
                # Find account by partner name
                accounts = org_client.list_accounts()["Accounts"]
                partner_account = None

                for account in accounts:
                    if args.partner_name == account["Name"]:  # Exact match
                        partner_account = account
                        break

                if not partner_account:
                    # Try to find similar names for helpful error message
                    similar_names = []
                    partner_name_lower = args.partner_name.lower()
                    for account in accounts:
                        account_name = account["Name"]
                        account_name_lower = account_name.lower()
                        # Check for partial matches - if either string contains a significant part of the other
                        # Split on common separators to find word matches
                        partner_words = set(
                            w
                            for w in partner_name_lower.replace("-", " ").replace("_", " ").split()
                            if w
                        )
                        account_words = set(
                            w
                            for w in account_name_lower.replace("-", " ").replace("_", " ").split()
                            if w
                        )
                        # If there's significant word overlap, consider it similar
                        if partner_words & account_words:  # Set intersection - any common words
                            similar_names.append(account_name)

                    error_msg = f"Partner account '{args.partner_name}' not found"
                    if similar_names:
                        error_msg += f". Did you mean one of these: {', '.join(similar_names[:3])}"
                    else:
                        error_msg += f". Available accounts: {len(accounts)} total"

                    raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, error_msg)

                account_id = partner_account["Id"]

            console.print("\nVerifying current account state...")
            recheck_response = org_client.describe_account(AccountId=account_id)
            recheck_account = recheck_response["Account"]

            # Check if account is already closed
            if (
                recheck_account["Status"] == "SUSPENDED"
                and recheck_account.get("State") == "CLOSED"
            ):
                return {
                    "Success": True,
                    "PartnerName": args.partner_name,
                    "AccountId": account_id,
                    "Status": "Already Closed",
                    "Message": f"Partner account '{args.partner_name}' is already closed",
                    "Note": "Account was previously suspended and closed.",
                }

            # Close the account
            try:
                org_client.close_account(AccountId=account_id)
            except ClientError as e:
                if e.response["Error"]["Code"] == "AccountAlreadyClosedException":
                    return {
                        "Success": True,
                        "PartnerName": args.partner_name,
                        "AccountId": account_id,
                        "Status": "Already Closed",
                        "Message": f"Partner account '{args.partner_name}' is already closed",
                        "Note": "Account was previously suspended and closed.",
                    }
                raise

            result = {
                "Success": True,
                "PartnerName": args.partner_name,
                "AccountId": account_id,
                "Status": "Suspended",
                "Message": f"Partner account '{args.partner_name}' has been suspended",
                "CleanupTasks": [
                    "Account suspended via AWS Organizations",
                    "Access to AWS services blocked",
                    "Billing stopped for new resources",
                ],
                "Note": "Account suspension is immediate. Full closure may take 90 days.",
            }

            return result

        except ClientError as e:
            raise TelcoCLIException(
                ErrorCode.AWS_API_ERROR, f"AWS error: {e.response['Error']['Message']}"
            )
        except TelcoCLIException:
            # Re-raise TelcoCLIException as-is to preserve original error codes
            raise
