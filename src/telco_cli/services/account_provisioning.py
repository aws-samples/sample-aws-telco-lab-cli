# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Account provisioning functionality for partner accounts.

# ============================================================================
# WARNING - DEMO CODE - NOT FOR PRODUCTION USE
# ============================================================================
# This module contains IAM policies with service-level wildcards (e.g., "ec2:*",
# "s3:*", "eks:*") that are INTENTIONALLY broad for demonstration and lab
# environments.
#
# FOR PRODUCTION USE:
# - Replace wildcards with specific actions required for your use case
# - Follow AWS IAM best practices for least privilege
# - Use AWS IAM Access Analyzer to identify required permissions
# - See: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
# ============================================================================
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.utils import get_logger

logger = get_logger(__name__)


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


class AccountProvisioningEngine:
    """Engine for provisioning partner accounts."""

    def __init__(self):
        """Initialize the provisioning engine."""
        self.org_client = boto3.client("organizations")
        self.iam_client = boto3.client("iam")
        self.sts_client = boto3.client("sts")

    def provision_partner_account(
        self, request: AccountProvisioningRequest
    ) -> AccountProvisioningResult:
        """Provision a complete partner account."""
        start_time = time.time()

        try:
            logger.info(f"Creating AWS Organizations account: {request.account_name}")
            account_id = self._create_organizations_account(request)
            logger.info(f"Account created: {account_id}")

            logger.info("Creating IAM configuration...")
            iam_result = self._create_iam_setup(request, account_id)

            self._tag_account(account_id, request)

            provisioning_time = time.time() - start_time

            return AccountProvisioningResult(
                success=True,
                aws_account_id=account_id,
                account_name=request.account_name,
                cross_account_role_arn=iam_result["role_arn"],
                provisioning_time_seconds=provisioning_time,
                role_result=iam_result,
            )

        except ClientError as e:
            logger.error(f"AWS error during provisioning: {e}")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, str(e))
        except TelcoCLIException:
            raise
        except Exception as e:
            logger.exception("Unexpected error during provisioning")
            raise TelcoCLIException(ErrorCode.PARTNER_CREATION_FAILED, str(e))

    def _create_organizations_account(self, request: AccountProvisioningRequest) -> str:
        """Create account in AWS Organizations.

        Returns:
            str: The created account ID

        Raises:
            TelcoCLIException: If account creation fails
        """
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
                    return account_id
                elif status == "FAILED":
                    failure_reason = status_response["CreateAccountStatus"].get(
                        "FailureReason", "Unknown"
                    )
                    raise TelcoCLIException(
                        ErrorCode.PARTNER_CREATION_FAILED,
                        f"Account creation failed: {failure_reason}",
                    )

                time.sleep(10)
                wait_time += 10

            raise TelcoCLIException(ErrorCode.PARTNER_CREATION_FAILED, "Account creation timed out")

        except ClientError as e:
            logger.error(f"AWS error creating account: {e}")
            raise TelcoCLIException(
                ErrorCode.AWS_API_ERROR, f"AWS error: {e.response['Error']['Message']}"
            )
        except TelcoCLIException:
            raise
        except Exception as e:
            logger.exception("Unexpected error creating Organizations account")
            raise TelcoCLIException(ErrorCode.PARTNER_CREATION_FAILED, str(e))

    def _create_iam_setup(
        self, request: AccountProvisioningRequest, account_id: str
    ) -> Dict[str, Any]:
        """Create comprehensive IAM setup in target account with boundaries and multiple roles.

        Raises:
            TelcoCLIException: If IAM setup fails
        """
        try:
            partner_upper: str = request.partner_name.upper()
            logger.info(f"Setting up IAM in target account {account_id}")

            # Step 1: Assume role in target account (includes security check)
            target_credentials: Dict[str, str] = self._assume_role_in_target_account(account_id)
            target_iam_client = boto3.client(
                "iam",
                aws_access_key_id=target_credentials["AccessKeyId"],
                aws_secret_access_key=target_credentials["SecretAccessKey"],
                aws_session_token=target_credentials["SessionToken"],
            )

            # Step 2: Create permission boundary policy
            boundary_policy_arn: str = self._create_boundary_policy(
                target_iam_client, partner_upper, account_id
            )

            # Step 3: Create multiple roles based on account type
            roles_created: List[Dict[str, Any]] = self._create_partner_roles(
                target_iam_client,
                partner_upper,
                request.account_type,
                account_id,
                request.partner_account_id,
                boundary_policy_arn,
            )

            # Step 4: Create JDA admin role if admin account IDs provided
            if request.admin_account_ids:
                jda_admin_role = self._create_jda_admin_role(
                    target_iam_client,
                    partner_upper,
                    account_id,
                    request.admin_account_ids,
                )
                roles_created.append(jda_admin_role)

            # Return primary role for backward compatibility
            primary_role: Optional[Dict[str, Any]] = roles_created[0] if roles_created else None

            return {
                "success": True,
                "role_arn": primary_role["role_arn"] if primary_role else None,
                "role_name": primary_role["role_name"] if primary_role else None,
                "roles_created": roles_created,
                "boundary_policy_arn": boundary_policy_arn,
                "target_account_id": account_id,
            }

        except Exception as e:
            logger.error(f"Failed to create IAM setup: {e}")
            raise TelcoCLIException(
                ErrorCode.PARTNER_CREATION_FAILED, f"IAM setup failed: {str(e)}"
            )

    def _assume_role_in_target_account(self, account_id: str) -> Dict[str, str]:
        """Assume OrganizationAccountAccessRole in target account.

        Args:
            account_id: Target AWS account ID

        Returns:
            Dict containing AWS credentials

        Raises:
            Exception: If role assumption fails or same account access attempted
        """
        try:
            # Security check: Validate we're not trying to assume role in same account
            current_account: str = self.sts_client.get_caller_identity()["Account"]
            if account_id == current_account:
                raise Exception(
                    f"Cannot assume role in same account {account_id}. "
                    "Target account must be different from current account."
                )

            role_arn: str = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
            logger.info(f"Assuming role {role_arn} from account {current_account}")

            response = self.sts_client.assume_role(
                RoleArn=role_arn, RoleSessionName="telcocli-partner-setup"
            )
            logger.info(f"Successfully assumed role in target account {account_id}")
            return response["Credentials"]
        except Exception as e:
            logger.error(f"Failed to assume role in target account {account_id}: {e}")
            raise

    def _create_boundary_policy(self, iam_client, partner_name: str, account_id: str) -> str:
        """Create permission boundary policy in target account."""
        try:
            policy_name = f"{partner_name}-Boundary"
            boundary_policy = self._get_boundary_policy_template(account_id)

            try:
                policy_response = iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(boundary_policy),
                    Description=f"Permission boundary for {partner_name} partner access",
                )
                logger.info(f"Created boundary policy: {policy_name}")
                return policy_response["Policy"]["Arn"]
            except iam_client.exceptions.EntityAlreadyExistsException:
                logger.info(f"Boundary policy already exists: {policy_name}")
                return f"arn:aws:iam::{account_id}:policy/{policy_name}"

        except Exception as e:
            logger.error(f"Failed to create boundary policy: {e}")
            raise

    def _create_partner_roles(
        self,
        iam_client,
        partner_name: str,
        account_type: str,
        account_id: str,
        partner_account_id: str,
        boundary_policy_arn: str,
    ) -> List[Dict[str, Any]]:
        """Create multiple roles based on account type."""
        roles_created = []

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": f"arn:aws:iam::{partner_account_id}:root"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        # Get role definitions for account type
        role_definitions = self._get_role_definitions_for_account_type(account_type)

        for role_def in role_definitions:
            role_name = f"{partner_name}-{role_def['suffix']}"

            try:
                # Create role with boundary
                iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=f"{role_def['description']} for {partner_name} partner",
                    PermissionsBoundary=boundary_policy_arn,
                )
                logger.info(f"Created role: {role_name}")

                # Create and attach policies for this role
                policies_created = []
                for policy_template in role_def["policies"]:
                    policy_name = f"{partner_name}-{policy_template['name']}"
                    policy_arn = self._create_policy_if_not_exists(
                        iam_client,
                        policy_name,
                        account_id,
                        policy_template["template"](account_id),
                        policy_template["description"],
                    )
                    policies_created.append(policy_arn)

                # Attach policies to role
                self._attach_policies_to_role(iam_client, role_name, policies_created)

                roles_created.append(
                    {
                        "role_name": role_name,
                        "role_arn": f"arn:aws:iam::{account_id}:role/{role_name}",
                        "role_type": role_def["type"],
                        "policies": policies_created,
                        "switch_role_url": f"https://signin.aws.amazon.com/switchrole?account={account_id}&roleName={role_name}&displayName={partner_name}-{role_def['type']}",
                    }
                )

            except iam_client.exceptions.EntityAlreadyExistsException:
                logger.info(f"Role already exists: {role_name}")
                roles_created.append(
                    {
                        "role_name": role_name,
                        "role_arn": f"arn:aws:iam::{account_id}:role/{role_name}",
                        "role_type": role_def["type"],
                        "policies": [],
                        "switch_role_url": f"https://signin.aws.amazon.com/switchrole?account={account_id}&roleName={role_name}&displayName={partner_name}-{role_def['type']}",
                    }
                )

        return roles_created

    def _create_jda_admin_role(
        self,
        iam_client,
        partner_name: str,
        account_id: str,
        admin_account_ids: List[str],
    ) -> Dict[str, Any]:
        """Create JDA admin role with full administrator access."""
        role_name = f"{partner_name}-JDA-Admin"

        # Create trust policy for admin accounts
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            f"arn:aws:iam::{admin_account_id}:root"
                            for admin_account_id in admin_account_ids
                        ]
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }

        try:
            # Create role
            iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"JDA Admin access for {partner_name} partner accounts",
            )
            logger.info(f"Created JDA admin role: {role_name}")

            # Attach AdministratorAccess policy
            iam_client.attach_role_policy(
                RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess"
            )
            logger.info(f"Attached AdministratorAccess policy to {role_name}")

            return {
                "role_name": role_name,
                "role_arn": f"arn:aws:iam::{account_id}:role/{role_name}",
                "role_type": "JDA-Admin",
                "policies": ["arn:aws:iam::aws:policy/AdministratorAccess"],
                "switch_role_url": f"https://signin.aws.amazon.com/switchrole?account={account_id}&roleName={role_name}&displayName={partner_name}-JDA-Admin",
            }

        except iam_client.exceptions.EntityAlreadyExistsException:
            logger.info(f"JDA admin role already exists: {role_name}")
            return {
                "role_name": role_name,
                "role_arn": f"arn:aws:iam::{account_id}:role/{role_name}",
                "role_type": "JDA-Admin",
                "policies": [],
                "switch_role_url": f"https://signin.aws.amazon.com/switchrole?account={account_id}&roleName={role_name}&displayName={partner_name}-JDA-Admin",
            }

    def _get_role_definitions_for_account_type(self, account_type: str) -> List[Dict[str, Any]]:
        """Get role definitions based on account type."""
        if account_type == "joint-developer":
            return [
                {
                    "type": "Admin",
                    "suffix": "Admin",
                    "description": "Administrative access for joint development",
                    "policies": [
                        {
                            "name": "JointDevAdminPolicy",
                            "template": self._get_joint_dev_admin_policy_template,
                            "description": "Joint development administrative permissions",
                        }
                    ],
                }
            ]
        elif account_type == "sandbox":
            return [
                {
                    "type": "SandboxAdmin",
                    "suffix": "SandboxAdmin",
                    "description": "Full sandbox administration",
                    "policies": [
                        {
                            "name": "SandboxPolicy",
                            "template": self._get_sandbox_policy_template,
                            "description": "Sandbox development permissions",
                        }
                    ],
                }
            ]
        elif account_type == "production":
            return [
                {
                    "type": "ReadOnly",
                    "suffix": "ReadOnly",
                    "description": "Production read-only access",
                    "policies": [
                        {
                            "name": "ProductionReadOnlyPolicy",
                            "template": self._get_production_policy_template,
                            "description": "Production read-only permissions",
                        }
                    ],
                }
            ]
        else:
            # Default fallback
            return [
                {
                    "type": "BasicAccess",
                    "suffix": "BasicAccess",
                    "description": "Basic access",
                    "policies": [
                        {
                            "name": "BasicAccessPolicy",
                            "template": self._get_basic_access_policy_template,
                            "description": "Basic access permissions",
                        }
                    ],
                }
            ]

    def _create_policy_if_not_exists(
        self,
        iam_client,
        policy_name: str,
        account_id: str,
        policy_document: Dict[str, Any],
        description: str,
    ) -> str:
        """Create policy if it doesn't exist, return ARN."""
        try:
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description=description,
            )
            logger.info(f"Created policy: {policy_name}")
            return policy_response["Policy"]["Arn"]
        except iam_client.exceptions.EntityAlreadyExistsException:
            logger.info(f"Policy already exists: {policy_name}")
            return f"arn:aws:iam::{account_id}:policy/{policy_name}"

    def _attach_policies_to_role(self, iam_client, role_name: str, policy_arns: List[str]) -> None:
        """Attach policies to role."""
        for policy_arn in policy_arns:
            try:
                iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                logger.info(f"Attached policy {policy_arn} to role {role_name}")
            except Exception as e:
                logger.error(f"Failed to attach policy {policy_arn} to role {role_name}: {e}")
                raise

    def _tag_account(self, account_id: str, request: AccountProvisioningRequest) -> None:
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

        except Exception:
            logger.error("Failed to tag account")

    def list_partner_accounts(self) -> List[Dict[str, Any]]:
        """List all partner accounts."""
        # Placeholder implementation
        return []

    def get_partner_account(self, partner_name: str) -> Dict[str, Any]:
        """Get partner account details."""
        # Placeholder implementation
        return {"partner_name": partner_name, "status": "not_found"}

    def _get_boundary_policy_template(self, account_id: str) -> Dict[str, Any]:
        """Get permission boundary policy template.

        WARNING - DEMO CODE: This policy uses service-level wildcards (ec2:*, s3:*, etc.)
        for demonstration purposes. For production, replace with specific actions.
        """
        # WARNING: Service wildcards below are for DEMO/LAB use only.
        # For production, enumerate specific actions required.
        template = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "EKSadmin",
                    "Effect": "Allow",
                    "Action": [
                        "eks:*",
                        "ec2:CreateLaunchTemplate",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["ssm:*", "sts:AssumeRole", "s3:*"],
                    "Resource": "*",
                },
                {"Effect": "Allow", "Action": ["cloudformation:*"], "Resource": "*"},
                {
                    "Effect": "Allow",
                    "Action": ["autoscaling:*", "sqs:*", "sns:*"],
                    "Resource": "*",
                },
                {
                    "Sid": "Statement1",
                    "Effect": "Allow",
                    "Action": ["iam:PassRole"],
                    "Resource": [f"arn:aws:iam::{account_id}:role/SSMInstanceProfile"],
                },
                {
                    "Effect": "Allow",
                    "Action": ["ssmmessages:*", "ec2messages:*"],
                    "Resource": "*",
                },
                {
                    "Sid": "BlockIAM",
                    "Effect": "Deny",
                    "Action": [
                        "iam:createRole*",
                        "iam:createPol*",
                        "iam:*rolePol*",
                        "iam:AttachGroupPolicy",
                        "iam:AttachUserPolicy",
                        "iam:DeleteRolePermissionsBoundary",
                        "iam:DeleteUserPermissionsBoundary",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["ec2:*"],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["ecr:*"],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["iam:CreateServiceLinkedRole"],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {"iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"}
                    },
                },
                {
                    "Effect": "Allow",
                    "Action": ["elasticfilesystem:*"],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "cognito-idp:*",
                        "acm:*",
                        "iam:ListServerCertificates",
                        "iam:GetServerCertificate",
                        "wafv2:*",
                        "waf:*",
                        "shield:*",
                        "route53:*",
                        "iam:ListInstanceProfiles",
                        "iam:GetInstanceProfile",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["elasticloadbalancing:*"],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": ["logs:*", "tag:*"],
                    "Resource": "*",
                },
            ],
        }
        return template

    def _get_joint_dev_admin_policy_template(self, account_id: str) -> Dict[str, Any]:
        """Get joint development admin policy template.

        WARNING - DEMO CODE: This policy uses service-level wildcards (outposts:*, etc.)
        for demonstration purposes. For production, replace with specific actions.
        """
        # WARNING: Service wildcards below are for DEMO/LAB use only.
        # For production, enumerate specific actions required.
        return {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": "outposts:*", "Resource": "*"},
                {
                    "Effect": "Deny",
                    "Action": ["iam:AttachRolePolicy", "iam:PutRolePolicy"],
                    "Resource": f"arn:aws:iam::{account_id}:role/Ericsson-5GC-AssumeRole",
                },
                {
                    "Effect": "Deny",
                    "Action": ["iam:createRole"],
                    "Resource": "*",
                    "Condition": {
                        "ArnNotEquals": {
                            "iam:PermissionsBoundary": f"arn:aws:iam::{account_id}:policy/Ericsson-Boundary"
                        }
                    },
                },
                {
                    "Sid": "AllowSpecificIAMOperations",
                    "Effect": "Allow",
                    "Action": [
                        # Role management (limited by deny statements above)
                        "iam:CreateRole",
                        "iam:DeleteRole",
                        "iam:GetRole",
                        "iam:ListRoles",
                        "iam:UpdateRole",
                        "iam:TagRole",
                        "iam:UntagRole",
                        # Policy management
                        "iam:CreatePolicy",
                        "iam:DeletePolicy",
                        "iam:GetPolicy",
                        "iam:GetPolicyVersion",
                        "iam:ListPolicies",
                        "iam:ListPolicyVersions",
                        "iam:CreatePolicyVersion",
                        "iam:DeletePolicyVersion",
                        "iam:SetDefaultPolicyVersion",
                        # Role policy attachments (limited by deny statements)
                        "iam:AttachRolePolicy",
                        "iam:DetachRolePolicy",
                        "iam:PutRolePolicy",
                        "iam:DeleteRolePolicy",
                        "iam:GetRolePolicy",
                        "iam:ListRolePolicies",
                        "iam:ListAttachedRolePolicies",
                        # Instance profiles (for EC2/EKS)
                        "iam:CreateInstanceProfile",
                        "iam:DeleteInstanceProfile",
                        "iam:GetInstanceProfile",
                        "iam:ListInstanceProfiles",
                        "iam:AddRoleToInstanceProfile",
                        "iam:RemoveRoleFromInstanceProfile",
                        # Service-linked roles
                        "iam:CreateServiceLinkedRole",
                        "iam:DeleteServiceLinkedRole",
                        "iam:GetServiceLinkedRoleDeletionStatus",
                        # OIDC providers (for EKS)
                        "iam:CreateOpenIDConnectProvider",
                        "iam:DeleteOpenIDConnectProvider",
                        "iam:GetOpenIDConnectProvider",
                        "iam:ListOpenIDConnectProviders",
                        "iam:TagOpenIDConnectProvider",
                        "iam:UntagOpenIDConnectProvider",
                        "iam:UpdateOpenIDConnectProviderThumbprint",
                        # Pass role (already has specific conditions below)
                        "iam:PassRole",
                        # Read-only operations
                        "iam:GetAccountSummary",
                        "iam:GetAccountPasswordPolicy",
                        "iam:ListAccountAliases",
                        "iam:GenerateServiceLastAccessedDetails",
                        "iam:GetServiceLastAccessedDetails",
                        # STS operations
                        "sts:AssumeRole",
                        "sts:GetCallerIdentity",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": "iam:CreateServiceLinkedRole",
                    "Resource": "arn:aws:iam::*:role/aws-service-role/*",
                },
                {
                    "Effect": "Allow",
                    "Action": "iam:PassRole",
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "iam:PassedToService": [
                                "eks.amazonaws.com",
                                "ec2.amazonaws.com",
                                "sqs.amazonaws.com",
                                "cloudformation.amazonaws.com",
                                "codebuild.amazonaws.com",
                                "events.amazonaws.com",
                            ]
                        }
                    },
                },
                {
                    "Effect": "Allow",
                    "Action": "iam:PassRole",
                    "Resource": [
                        f"arn:aws:iam::{account_id}:role/aws_sqs_queue_ec2_autoscaling_role",
                        f"arn:aws:iam::{account_id}:role/test-eks-cluster-role",
                        f"arn:aws:iam::{account_id}:role/Tnb*",
                        f"arn:aws:iam::{account_id}:role/AmazonEKSPodIdentityAmazonVPCCNIRole",
                    ],
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:*",
                        "autoscaling:*",
                        "eks:*",
                        "cloudformation:*",
                        "ecr:*",
                        "elasticloadbalancing:*",
                        "elasticfilesystem:*",
                        "kms:*",
                        "lambda:*",
                        "cloudshell:*",
                        "route53:*",
                        "ssm:*",
                        "sqs:*",
                        "logs:*",
                        "cloudwatch:*",
                        "s3:*",
                        "support:*",
                        "codebuild:*",
                        "events:*",
                        "grafana:*",
                        "rolesanywhere:*",
                        "sts:GetCallerIdentity",
                        "tag:GetResources",
                    ],
                    "Resource": "*",
                },
            ],
        }

    def _get_sandbox_policy_template(self, account_id: str) -> Dict[str, Any]:
        """Get sandbox policy template - broader permissions.

        WARNING - DEMO CODE: This policy uses service-level wildcards (ec2:*, s3:*, etc.)
        for demonstration purposes. For production, replace with specific actions.
        """
        # WARNING: Service wildcards below are for DEMO/LAB use only.
        # For production, enumerate specific actions required.
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:*",
                        "s3:*",
                        "logs:*",
                        "cloudwatch:*",
                        "eks:*",
                        "ecr:*",
                        "elasticloadbalancing:*",
                        "autoscaling:*",
                        "ssm:*",
                        "lambda:*",
                        "apigateway:*",
                        "dynamodb:*",
                    ],
                    "Resource": "*",
                },
                {
                    "Effect": "Allow",
                    "Action": "iam:PassRole",
                    "Resource": f"arn:aws:iam::{account_id}:role/*",
                    "Condition": {
                        "StringEquals": {
                            "iam:PassedToService": [
                                "eks.amazonaws.com",
                                "ec2.amazonaws.com",
                                "lambda.amazonaws.com",
                                "elasticloadbalancing.amazonaws.com",
                            ]
                        }
                    },
                },
            ],
        }

    def _get_production_policy_template(self, account_id: str) -> Dict[str, Any]:
        """Get production policy template - read-only permissions."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:Describe*",
                        "eks:Describe*",
                        "eks:List*",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:GetLogEvents",
                        "cloudwatch:GetMetricStatistics",
                        "cloudwatch:ListMetrics",
                        "cloudwatch:DescribeAlarms",
                    ],
                    "Resource": "*",
                }
            ],
        }

    def _get_basic_access_policy_template(self, account_id: str) -> Dict[str, Any]:
        """Get basic access policy template."""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:Describe*",
                        "s3:ListBucket",
                        "s3:GetObject",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "cloudwatch:GetMetricStatistics",
                    ],
                    "Resource": "*",
                }
            ],
        }
