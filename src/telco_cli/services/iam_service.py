# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""IAM service for partner account setup."""

import json
from typing import Any, Dict, List

import boto3

from telco_cli.utils import get_logger

logger = get_logger(__name__)


class IAMService:
    """Service for IAM operations in partner accounts."""

    def __init__(self):
        """Initialize the IAM service."""
        self.sts_client = boto3.client("sts")

    def setup_partner_iam(
        self, account_id: str, partner_name: str, partner_account_id: str, account_type: str
    ) -> Dict[str, Any]:
        """Create comprehensive IAM setup in target account."""
        try:
            # Prevent role creation in management/root account
            if self._is_management_account(account_id):
                return {
                    "success": False,
                    "error_message": (
                        f"Cannot create partner roles in management account {account_id}. "
                        "Roles must be created in target JDA accounts only."
                    ),
                }

            partner_upper = partner_name.upper()

            # Assume role in target account
            target_credentials = self._assume_role_in_target_account(account_id)
            target_iam_client = boto3.client(
                "iam",
                aws_access_key_id=target_credentials["AccessKeyId"],
                aws_secret_access_key=target_credentials["SecretAccessKey"],
                aws_session_token=target_credentials["SessionToken"],
            )

            # Create permission boundary policy
            boundary_policy_arn = self._create_boundary_policy(
                target_iam_client, partner_upper, account_id
            )

            # Create roles based on account type
            roles_created = self._create_partner_roles(
                target_iam_client,
                partner_upper,
                account_type,
                account_id,
                partner_account_id,
                boundary_policy_arn,
            )

            primary_role = roles_created[0] if roles_created else None

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
            return {"success": False, "error_message": str(e)}

    def _assume_role_in_target_account(self, account_id: str) -> Dict[str, str]:
        """Assume OrganizationAccountAccessRole in target account."""
        try:
            role_arn = f"arn:aws:iam::{account_id}:role/OrganizationAccountAccessRole"
            response = self.sts_client.assume_role(
                RoleArn=role_arn, RoleSessionName="telcocli-partner-setup"
            )
            logger.info(f"Assumed role in target account {account_id}")
            return response["Credentials"]
        except Exception as e:
            logger.error(f"Failed to assume role in account {account_id}: {e}")
            raise

    def _create_boundary_policy(self, iam_client, partner_upper: str, account_id: str) -> str:
        """Create permission boundary policy."""
        boundary_policy_name = f"{partner_upper}-PermissionBoundary"

        # SECURITY: Permission boundary with least privilege
        # This boundary allows common AWS operations while denying critical IAM and Organizations actions
        boundary_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCommonAWSServices",
                    "Effect": "Allow",
                    "Action": [
                        # EC2 and VPC operations
                        "ec2:Describe*",
                        "ec2:Get*",
                        "ec2:List*",
                        "ec2:CreateTags",
                        "ec2:DeleteTags",
                        "ec2:RunInstances",
                        "ec2:TerminateInstances",
                        "ec2:StartInstances",
                        "ec2:StopInstances",
                        "ec2:CreateSecurityGroup",
                        "ec2:DeleteSecurityGroup",
                        "ec2:AuthorizeSecurityGroupIngress",
                        "ec2:AuthorizeSecurityGroupEgress",
                        "ec2:RevokeSecurityGroupIngress",
                        "ec2:RevokeSecurityGroupEgress",
                        "ec2:CreateKeyPair",
                        "ec2:DeleteKeyPair",
                        "ec2:CreateVolume",
                        "ec2:DeleteVolume",
                        "ec2:AttachVolume",
                        "ec2:DetachVolume",
                        "ec2:CreateSnapshot",
                        "ec2:DeleteSnapshot",
                        # EKS operations
                        "eks:Describe*",
                        "eks:List*",
                        "eks:CreateCluster",
                        "eks:DeleteCluster",
                        "eks:UpdateClusterConfig",
                        "eks:CreateNodegroup",
                        "eks:DeleteNodegroup",
                        "eks:UpdateNodegroupConfig",
                        "eks:CreateAddon",
                        "eks:DeleteAddon",
                        "eks:UpdateAddon",
                        "eks:TagResource",
                        "eks:UntagResource",
                        # S3 operations
                        "s3:ListBucket",
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:GetBucketLocation",
                        "s3:GetBucketVersioning",
                        "s3:ListBucketVersions",
                        "s3:CreateBucket",
                        "s3:DeleteBucket",
                        "s3:PutBucketPolicy",
                        "s3:GetBucketPolicy",
                        "s3:DeleteBucketPolicy",
                        "s3:PutBucketTagging",
                        "s3:GetBucketTagging",
                        # CloudFormation operations
                        "cloudformation:Describe*",
                        "cloudformation:List*",
                        "cloudformation:Get*",
                        "cloudformation:CreateStack",
                        "cloudformation:UpdateStack",
                        "cloudformation:DeleteStack",
                        "cloudformation:CreateChangeSet",
                        "cloudformation:ExecuteChangeSet",
                        "cloudformation:DeleteChangeSet",
                        # Lambda operations
                        "lambda:List*",
                        "lambda:Get*",
                        "lambda:CreateFunction",
                        "lambda:DeleteFunction",
                        "lambda:UpdateFunctionCode",
                        "lambda:UpdateFunctionConfiguration",
                        "lambda:InvokeFunction",
                        "lambda:AddPermission",
                        "lambda:RemovePermission",
                        "lambda:TagResource",
                        "lambda:UntagResource",
                        # CloudWatch operations
                        "cloudwatch:Describe*",
                        "cloudwatch:List*",
                        "cloudwatch:Get*",
                        "cloudwatch:PutMetricData",
                        "cloudwatch:PutMetricAlarm",
                        "cloudwatch:DeleteAlarms",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:GetLogEvents",
                        "logs:FilterLogEvents",
                        # Auto Scaling operations
                        "autoscaling:Describe*",
                        "autoscaling:CreateAutoScalingGroup",
                        "autoscaling:UpdateAutoScalingGroup",
                        "autoscaling:DeleteAutoScalingGroup",
                        "autoscaling:CreateLaunchConfiguration",
                        "autoscaling:DeleteLaunchConfiguration",
                        "autoscaling:PutScalingPolicy",
                        "autoscaling:DeletePolicy",
                        # Elastic Load Balancing operations
                        "elasticloadbalancing:Describe*",
                        "elasticloadbalancing:CreateLoadBalancer",
                        "elasticloadbalancing:DeleteLoadBalancer",
                        "elasticloadbalancing:CreateTargetGroup",
                        "elasticloadbalancing:DeleteTargetGroup",
                        "elasticloadbalancing:RegisterTargets",
                        "elasticloadbalancing:DeregisterTargets",
                        "elasticloadbalancing:CreateListener",
                        "elasticloadbalancing:DeleteListener",
                        "elasticloadbalancing:ModifyListener",
                        # RDS operations
                        "rds:Describe*",
                        "rds:List*",
                        "rds:CreateDBInstance",
                        "rds:DeleteDBInstance",
                        "rds:ModifyDBInstance",
                        "rds:CreateDBSnapshot",
                        "rds:DeleteDBSnapshot",
                        "rds:RestoreDBInstanceFromDBSnapshot",
                        # DynamoDB operations
                        "dynamodb:Describe*",
                        "dynamodb:List*",
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:CreateTable",
                        "dynamodb:DeleteTable",
                        "dynamodb:UpdateTable",
                        # ECR operations
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:DescribeRepositories",
                        "ecr:ListImages",
                        "ecr:DescribeImages",
                        "ecr:CreateRepository",
                        "ecr:DeleteRepository",
                        "ecr:PutImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload",
                        # Systems Manager operations
                        "ssm:Describe*",
                        "ssm:Get*",
                        "ssm:List*",
                        "ssm:PutParameter",
                        "ssm:DeleteParameter",
                        "ssm:SendCommand",
                        "ssm:StartSession",
                        # Secrets Manager operations
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:ListSecrets",
                        "secretsmanager:CreateSecret",
                        "secretsmanager:DeleteSecret",
                        "secretsmanager:UpdateSecret",
                        # KMS operations
                        "kms:Describe*",
                        "kms:List*",
                        "kms:Get*",
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:GenerateDataKey",
                        "kms:CreateKey",
                        "kms:CreateAlias",
                        "kms:DeleteAlias",
                        # SNS operations
                        "sns:List*",
                        "sns:Get*",
                        "sns:CreateTopic",
                        "sns:DeleteTopic",
                        "sns:Subscribe",
                        "sns:Unsubscribe",
                        "sns:Publish",
                        # SQS operations
                        "sqs:List*",
                        "sqs:Get*",
                        "sqs:CreateQueue",
                        "sqs:DeleteQueue",
                        "sqs:SendMessage",
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        # STS operations (for assuming roles)
                        "sts:AssumeRole",
                        "sts:GetCallerIdentity",
                        # Read-only IAM operations (for viewing existing resources)
                        "iam:Get*",
                        "iam:List*",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "DenyOrganizationsAndAccountManagement",
                    "Effect": "Deny",
                    "Action": [
                        "organizations:*",
                        "account:*",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "DenyIAMRoleManipulation",
                    "Effect": "Deny",
                    "Action": [
                        "iam:CreateRole",
                        "iam:DeleteRole",
                        "iam:AttachRolePolicy",
                        "iam:DetachRolePolicy",
                        "iam:PutRolePolicy",
                        "iam:DeleteRolePolicy",
                        "iam:UpdateAssumeRolePolicy",
                        "iam:CreateUser",
                        "iam:DeleteUser",
                        "iam:CreateAccessKey",
                        "iam:DeleteAccessKey",
                        "iam:AttachUserPolicy",
                        "iam:DetachUserPolicy",
                        "iam:PutUserPolicy",
                        "iam:DeleteUserPolicy",
                    ],
                    "Resource": "*",
                },
            ],
        }

        try:
            response = iam_client.create_policy(
                PolicyName=boundary_policy_name,
                PolicyDocument=json.dumps(boundary_policy_document),
                Description=f"Permission boundary for {partner_upper} partner",
            )
            logger.info(f"Created boundary policy: {boundary_policy_name}")
            return response["Policy"]["Arn"]
        except iam_client.exceptions.EntityAlreadyExistsException:
            logger.info(f"Boundary policy already exists: {boundary_policy_name}")
            return f"arn:aws:iam::{account_id}:policy/{boundary_policy_name}"

    def _create_partner_roles(
        self,
        iam_client,
        partner_upper: str,
        account_type: str,
        account_id: str,
        partner_account_id: str,
        boundary_policy_arn: str,
    ) -> List[Dict[str, Any]]:
        """Create partner roles based on account type."""
        role_configs = self._get_role_configurations(account_type)
        roles_created = []

        for config in role_configs:
            role_name = f"{partner_upper}-{config['suffix']}"

            # Create assume role policy
            assume_role_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": f"arn:aws:iam::{partner_account_id}:root"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }

            try:
                # Create role
                role_response = iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                    Description=config["description"],
                    PermissionsBoundary=boundary_policy_arn,
                )

                role_arn = role_response["Role"]["Arn"]
                logger.info(f"Created role: {role_name}")

                roles_created.append(
                    {"role_name": role_name, "role_arn": role_arn, "type": config["type"]}
                )

            except Exception as e:
                logger.error(f"Failed to create role {role_name}: {e}")
                continue

        return roles_created

    def _is_management_account(self, account_id: str) -> bool:
        """Check if account is a management account that should not have partner roles."""
        try:
            # Try to get organization info to identify management account
            org_client = boto3.client("organizations")
            org_response = org_client.describe_organization()
            management_account_id = org_response["Organization"]["MasterAccountId"]

            if account_id == management_account_id:
                logger.warning(f"Account {account_id} is the management account")
                return True

            return False

        except Exception as e:
            logger.debug(f"Could not verify account type for {account_id}: {e}")
            # Default to allowing the operation if we can't determine account type
            return False

    def _get_role_configurations(self, account_type: str) -> List[Dict[str, Any]]:
        """Get role configurations based on account type."""
        if account_type == "joint-developer":
            return [
                {
                    "type": "JointDevAdmin",
                    "suffix": "JointDevAdmin",
                    "description": "Administrative access for joint development",
                }
            ]
        elif account_type == "sandbox":
            return [
                {
                    "type": "SandboxAdmin",
                    "suffix": "SandboxAdmin",
                    "description": "Full sandbox administration",
                }
            ]
        elif account_type == "production":
            return [
                {
                    "type": "ReadOnly",
                    "suffix": "ReadOnly",
                    "description": "Production read-only access",
                }
            ]
        else:
            return [{"type": "BasicAccess", "suffix": "BasicAccess", "description": "Basic access"}]
