# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""AWS Organizations service for account management."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from telco_cli.types.provisioning import AccountProvisioningRequest
from telco_cli.utils import get_logger

logger = get_logger(__name__)


class OrganizationsService:
    """Service for AWS Organizations operations."""

    def __init__(self):
        """Initialize the Organizations service."""
        self.org_client = boto3.client("organizations")

    def create_account(self, request: AccountProvisioningRequest) -> Dict[str, Any]:
        """Create account in AWS Organizations."""
        try:
            response = self.org_client.create_account(
                Email=request.contact_email, AccountName=request.account_name
            )

            create_account_request_id = response["CreateAccountStatus"]["Id"]

            logger.info("Waiting for account creation to complete...")
            max_wait_time = 300  # 5 minutes
            wait_time = 0

            while wait_time < max_wait_time:
                status_response = self.org_client.describe_create_account_status(
                    CreateAccountRequestId=create_account_request_id
                )

                status = status_response["CreateAccountStatus"]["State"]

                if status == "SUCCEEDED":
                    account_id = status_response["CreateAccountStatus"]["AccountId"]
                    return {"success": True, "account_id": account_id}
                elif status == "FAILED":
                    failure_reason = status_response["CreateAccountStatus"].get(
                        "FailureReason", "Unknown"
                    )
                    return {
                        "success": False,
                        "error_message": f"Account creation failed: {failure_reason}",
                    }

                time.sleep(10)
                wait_time += 10

            return {"success": False, "error_message": "Account creation timed out"}

        except ClientError as e:
            logger.error(f"AWS error creating account: {e}")
            return {
                "success": False,
                "error_message": f"AWS error: {e.response['Error']['Message']}",
            }
        except Exception as e:
            logger.exception("Unexpected error creating Organizations account")
            return {"success": False, "error_message": str(e)}

    def tag_account(self, account_id: str, request: AccountProvisioningRequest) -> None:
        """Tag the account with partner information."""
        try:
            tags = [
                {"Key": "Partner", "Value": request.partner_name},
                {"Key": "ManagedBy", "Value": "telcocli"},
                {"Key": "AccountType", "Value": request.account_type},
                {"Key": "CreatedAt", "Value": datetime.now(timezone.utc).isoformat()},
                {"Key": "Status", "Value": "Active"},
            ]

            self.org_client.tag_resource(ResourceId=account_id, Tags=tags)
            logger.info("Tagged account with partner information")

        except Exception as e:
            logger.error(f"Failed to tag account: {str(e)}")
            raise

    def list_partner_accounts(self) -> List[Dict[str, Any]]:
        """List all partner accounts managed by telcocli."""
        try:
            logger.info("Listing all accounts in organization")
            paginator = self.org_client.get_paginator("list_accounts")
            partner_accounts = []

            for page in paginator.paginate():
                for account in page["Accounts"]:
                    account_id = account["Id"]

                    # Get account tags to identify partner accounts
                    try:
                        tags_response = self.org_client.list_tags_for_resource(
                            ResourceId=account_id
                        )
                        tags = {tag["Key"]: tag["Value"] for tag in tags_response["Tags"]}

                        # Check if this is a partner account managed by telcocli
                        if tags.get("ManagedBy") == "telcocli" and "Partner" in tags:
                            account_info = {
                                "Id": account_id,
                                "Name": account["Name"],
                                "Email": account["Email"],
                                "Status": account["Status"],
                                "Partner": tags.get("Partner"),
                                "AccountType": tags.get("AccountType"),
                                "CreatedAt": tags.get("CreatedAt"),
                            }
                            partner_accounts.append(account_info)
                    except ClientError:
                        # Skip accounts we can't access tags for
                        logger.debug(f"Cannot access tags for account {account_id}")
                        continue

            logger.info(f"Found {len(partner_accounts)} partner accounts")
            return partner_accounts

        except ClientError as e:
            logger.error(f"AWS error listing accounts: {e}")
            raise
        except Exception:
            logger.exception("Unexpected error listing partner accounts")
            raise

    def get_partner_account(self, partner_name: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific partner account."""
        try:
            logger.info(f"Looking for partner account: {partner_name}")
            partner_accounts = self.list_partner_accounts()

            for account in partner_accounts:
                if account.get("Partner", "").lower() == partner_name.lower():
                    logger.info(f"Found partner account for {partner_name}")
                    return account

            logger.info(f"Partner account not found: {partner_name}")
            return None

        except Exception:
            logger.exception(f"Error getting partner account {partner_name}")
            raise
