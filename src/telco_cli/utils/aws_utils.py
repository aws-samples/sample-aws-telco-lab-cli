# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
AWS utility functions for TelcoCLI.

This module provides common AWS operations and utilities
used across different commands.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

try:
    from mypy_boto3_ec2 import EC2Client
    from mypy_boto3_iam import IAMClient
    from mypy_boto3_organizations import OrganizationsClient
    from mypy_boto3_sts import STSClient
except ImportError:
    # Fallback for environments without boto3-stubs
    STSClient = Any
    OrganizationsClient = Any
    IAMClient = Any
    EC2Client = Any

logger = logging.getLogger(__name__)


class AWSClientManager:
    """Manages AWS client creation and session handling."""

    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None):
        """Initialize AWS client manager."""
        self.profile = profile
        self.region = region
        self._session: Optional[boto3.Session] = None
        self._clients: Dict[str, Any] = {}

    def get_session(self) -> boto3.Session:
        """Get or create AWS session."""
        if self._session is None:
            session_kwargs = {}
            if self.profile:
                session_kwargs["profile_name"] = self.profile
            if self.region:
                session_kwargs["region_name"] = self.region

            try:
                self._session = boto3.Session(**session_kwargs)
                # Test the session
                if self._session is not None:
                    sts_client: STSClient = self._session.client("sts")
                identity = sts_client.get_caller_identity()
                logger.info(
                    f"Using AWS Account: {identity['Account']} (User: {identity.get('Arn', 'Unknown')})"
                )
            except (NoCredentialsError, ProfileNotFound) as e:
                logger.error(f"AWS credentials not found or invalid: {e}")
                raise ValueError(f"AWS credentials error: {e}")
            except ClientError as e:
                logger.error(f"Failed to get caller identity: {e}")
                raise ValueError(f"AWS session error: {e}")
            except Exception as e:
                logger.error(f"Failed to create AWS session: {e}")
                raise ValueError(f"AWS session error: {e}")

        return self._session

    def get_client(self, service_name: str) -> Any:
        """Get AWS service client."""
        if service_name not in self._clients:
            session = self.get_session()
            self._clients[service_name] = session.client(service_name)
        return self._clients[service_name]

    def get_resource(self, service_name: str) -> Any:
        """Get AWS service resource."""
        if service_name not in self._clients:
            session = self.get_session()
            self._clients[service_name] = session.resource(service_name)
        return self._clients[service_name]


class OrganizationsHelper:
    """Helper class for AWS Organizations operations."""

    def __init__(self, client_manager: AWSClientManager):
        """Initialize Organizations helper."""
        self.client_manager = client_manager
        self._org_client: Optional[OrganizationsClient] = None

    @property
    def org_client(self) -> OrganizationsClient:
        """Get Organizations client."""
        if self._org_client is None:
            self._org_client = self.client_manager.get_client("organizations")
        return self._org_client

    def create_account(
        self, account_name: str, email: str, role_name: str = "OrganizationAccountAccessRole"
    ) -> Dict[str, Any]:
        """Create a new AWS account in the organization."""
        try:
            response = self.org_client.create_account(
                AccountName=account_name, Email=email, RoleName=role_name
            )
            return response
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            raise ValueError(f"Failed to create account: {error_code} - {error_message}")

    def describe_account(self, account_id: str) -> Dict[str, Any]:
        """Get account details."""
        try:
            response = self.org_client.describe_account(AccountId=account_id)
            return response["Account"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccountNotFoundException":
                raise ValueError(f"Account {account_id} not found in organization")
            raise ValueError(f"Failed to describe account: {e.response['Error']['Message']}")

    def list_accounts(self) -> List[Dict[str, Any]]:
        """List all accounts in the organization."""
        try:
            accounts = []
            paginator = self.org_client.get_paginator("list_accounts")
            for page in paginator.paginate():
                accounts.extend(page["Accounts"])
            return accounts
        except ClientError as e:
            raise ValueError(f"Failed to list accounts: {e.response['Error']['Message']}")

    def create_organizational_unit(self, parent_id: str, name: str) -> Dict[str, Any]:
        """Create an organizational unit."""
        try:
            response = self.org_client.create_organizational_unit(ParentId=parent_id, Name=name)
            return response["OrganizationalUnit"]
        except ClientError as e:
            raise ValueError(f"Failed to create OU: {e.response['Error']['Message']}")

    def move_account(
        self, account_id: str, source_parent_id: str, destination_parent_id: str
    ) -> None:
        """Move account to different OU."""
        try:
            self.org_client.move_account(
                AccountId=account_id,
                SourceParentId=source_parent_id,
                DestinationParentId=destination_parent_id,
            )
        except ClientError as e:
            raise ValueError(f"Failed to move account: {e.response['Error']['Message']}")


class IAMHelper:
    """Helper class for IAM operations."""

    def __init__(self, client_manager: AWSClientManager):
        """Initialize IAM helper."""
        self.client_manager = client_manager
        self._iam_client: Optional[IAMClient] = None

    @property
    def iam_client(self) -> IAMClient:
        """Get IAM client."""
        if self._iam_client is None:
            self._iam_client = self.client_manager.get_client("iam")
        return self._iam_client

    def create_cross_account_role(
        self, role_name: str, trusted_account_id: str, policy_arns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a cross-account assume role."""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{trusted_account_id}:root"},
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {"sts:ExternalId": f"telco-{trusted_account_id}"}
                    },
                }
            ],
        }

        try:
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Cross-account role for partner account {trusted_account_id}",
                MaxSessionDuration=3600,
            )

            # Attach policies
            if policy_arns:
                for policy_arn in policy_arns:
                    self.iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)

            return response["Role"]

        except ClientError as e:
            raise ValueError(
                f"Failed to create cross-account role: {e.response['Error']['Message']}"
            )

    def delete_role(self, role_name: str) -> None:
        """Delete IAM role and detach all policies."""
        try:
            # List and detach attached policies
            response = self.iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in response["AttachedPolicies"]:
                self.iam_client.detach_role_policy(
                    RoleName=role_name, PolicyArn=policy["PolicyArn"]
                )

            # Delete inline policies
            response = self.iam_client.list_role_policies(RoleName=role_name)
            for policy_name in response["PolicyNames"]:
                self.iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)

            # Delete role
            self.iam_client.delete_role(RoleName=role_name)

        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchEntity":
                raise ValueError(f"Failed to delete role: {e.response['Error']['Message']}")


class EC2Helper:
    """Helper class for EC2 operations."""

    def __init__(self, client_manager: AWSClientManager):
        """Initialize EC2 helper."""
        self.client_manager = client_manager
        self._ec2_client: Optional[EC2Client] = None

    @property
    def ec2_client(self) -> EC2Client:
        """Get EC2 client."""
        if self._ec2_client is None:
            self._ec2_client = self.client_manager.get_client("ec2")
        return self._ec2_client

    def describe_dedicated_hosts(
        self, host_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Describe dedicated hosts."""
        try:
            kwargs = {}
            if host_ids:
                kwargs["HostIds"] = host_ids

            response = self.ec2_client.describe_hosts(**kwargs)
            return response["Hosts"]

        except ClientError as e:
            raise ValueError(
                f"Failed to describe dedicated hosts: {e.response['Error']['Message']}"
            )

    def allocate_hosts(
        self, instance_type: str, quantity: int, availability_zone: str
    ) -> List[str]:
        """Allocate dedicated hosts."""
        try:
            response = self.ec2_client.allocate_hosts(
                InstanceType=instance_type, Quantity=quantity, AvailabilityZone=availability_zone
            )
            return response["HostIds"]

        except ClientError as e:
            raise ValueError(f"Failed to allocate hosts: {e.response['Error']['Message']}")

    def release_hosts(self, host_ids: List[str]) -> None:
        """Release dedicated hosts."""
        try:
            self.ec2_client.release_hosts(HostIds=host_ids)
        except ClientError as e:
            raise ValueError(f"Failed to release hosts: {e.response['Error']['Message']}")


def validate_aws_account_id(account_id: str) -> bool:
    """Validate AWS account ID format."""
    import re

    return bool(re.match(r"^\d{12}$", account_id))


def format_aws_error(error: ClientError) -> str:
    """Format AWS ClientError for user-friendly display."""
    import html

    error_code = html.escape(error.response["Error"]["Code"])
    error_message = html.escape(error.response["Error"]["Message"])
    return f"{error_code}: {error_message}"


def get_caller_identity(client_manager: AWSClientManager) -> Dict[str, Any]:
    """Get current AWS caller identity."""
    try:
        sts_client = client_manager.get_client("sts")
        return sts_client.get_caller_identity()
    except ClientError as e:
        raise ValueError(f"Failed to get caller identity: {format_aws_error(e)}")


def check_aws_permissions(
    client_manager: AWSClientManager, required_permissions: List[str]
) -> Dict[str, bool]:
    """Check if current user has required permissions."""
    # This is a simplified check - in production, you'd use IAM policy simulator
    # or attempt actual operations to verify permissions

    results = {}
    for permission in required_permissions:
        # For now, assume all permissions are available
        # In a real implementation, you'd check each permission
        results[permission] = True

    return results
