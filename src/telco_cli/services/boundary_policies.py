# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Permission Boundary Policies for Partner Accounts

This module defines permission boundary policies that act as maximum permission
filters for partner IAM roles, based on JDA-style security model.

# ============================================================================
# WARNING - DEMO CODE - NOT FOR PRODUCTION USE
# ============================================================================
# This module contains service-level wildcards (e.g., "ec2:*", "s3:*", "eks:*")
# that are INTENTIONALLY broad for demonstration and lab environments.
#
# FOR PRODUCTION USE:
# - Replace wildcards with specific actions required for your use case
# - Follow AWS IAM best practices for least privilege
# - Use AWS IAM Access Analyzer to identify required permissions
# - See: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
# ============================================================================
"""

from typing import Any, Dict, List


def get_jda_boundary_policy(partner_name: str, account_id: str) -> Dict[str, Any]:
    """
    Get JDA-style permission boundary policy.

    This boundary policy allows broad permissions for telco lab operations
    but denies critical administrative actions that could compromise security.

    WARNING - DEMO CODE: This policy uses service-level wildcards (ec2:*, s3:*, etc.)
    for demonstration purposes. For production, replace with specific actions.

    Args:
        partner_name: Partner name (e.g., 'nokia', 'ericsson')
        account_id: AWS account ID where the boundary will be applied

    Returns:
        Dict: IAM policy document for permission boundary
    """
    # WARNING: Service wildcards below are for DEMO/LAB use only.
    # For production, enumerate specific actions required.
    boundary_policy = {
        "Version": "2012-10-17",
        "Statement": [
            # Allow most AWS services for development and testing
            {
                "Effect": "Allow",
                "Action": [
                    # EC2 and networking - full access for lab operations
                    "ec2:*",
                    "autoscaling:*",
                    "elasticloadbalancing:*",
                    "route53:*",
                    "directconnect:*",
                    "globalaccelerator:*",
                    # EKS and container services
                    "eks:*",
                    "ecr:*",
                    "ecs:*",
                    # Storage services
                    "s3:*",
                    "elasticfilesystem:*",
                    "fsx:*",
                    # Monitoring and logging
                    "logs:*",
                    "cloudwatch:*",
                    "xray:*",
                    "cloudtrail:Get*",
                    "cloudtrail:List*",
                    "cloudtrail:Describe*",
                    # Outposts - critical for telco lab
                    "outposts:*",
                    # Application services
                    "lambda:*",
                    "apigateway:*",
                    "events:*",
                    "sns:*",
                    "sqs:*",
                    # Database services
                    "rds:*",
                    "dynamodb:*",
                    "elasticache:*",
                    "redshift:*",
                    # Security services (read-only)
                    "iam:Get*",
                    "iam:List*",
                    "iam:Generate*",
                    "kms:Decrypt",
                    "kms:DescribeKey",
                    "kms:Encrypt",
                    "kms:GenerateDataKey*",
                    "kms:List*",
                    "kms:Get*",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecrets",
                    # CloudFormation
                    "cloudformation:*",
                    # Systems Manager
                    "ssm:*",
                    # Resource management
                    "resource-groups:*",
                    "tag:*",
                    # Cost and billing (read-only)
                    "ce:*",
                    "cur:*",
                    "budgets:View*",
                    # Support
                    "support:*",
                    # Service discovery
                    "servicediscovery:*",
                    # Transit Gateway for networking
                    "ec2:*TransitGateway*",
                    # VPC and networking
                    "ec2:*Vpc*",
                    "ec2:*Subnet*",
                    "ec2:*RouteTable*",
                    "ec2:*SecurityGroup*",
                    "ec2:*NetworkAcl*",
                    "ec2:*InternetGateway*",
                    "ec2:*NatGateway*",
                    # Identity services (limited)
                    "sts:GetCallerIdentity",
                    "sts:GetSessionToken",
                    "sts:DecodeAuthorizationMessage",
                ],
                "Resource": "*",
            },
            # Deny dangerous administrative actions
            {
                "Effect": "Deny",
                "Action": [
                    # IAM administrative actions
                    "iam:CreateUser",
                    "iam:DeleteUser",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:AttachUserPolicy",
                    "iam:DetachUserPolicy",
                    "iam:AttachRolePolicy",
                    "iam:DetachRolePolicy",
                    "iam:PutUserPolicy",
                    "iam:PutRolePolicy",
                    "iam:DeleteUserPolicy",
                    "iam:DeleteRolePolicy",
                    "iam:CreatePolicy",
                    "iam:DeletePolicy",
                    "iam:CreatePolicyVersion",
                    "iam:DeletePolicyVersion",
                    "iam:SetDefaultPolicyVersion",
                    "iam:CreateAccessKey",
                    "iam:DeleteAccessKey",
                    "iam:UpdateAccessKey",
                    "iam:CreateLoginProfile",
                    "iam:DeleteLoginProfile",
                    "iam:UpdateLoginProfile",
                    "iam:ChangePassword",
                    "iam:CreateServiceLinkedRole",
                    "iam:DeleteServiceLinkedRole",
                    # Organizations - prevent account manipulation
                    "organizations:*",
                    # Account management - use proper service names
                    "aws-portal:*",
                    # Billing and cost management (write operations)
                    "aws-portal:*",
                    "budgets:Create*",
                    "budgets:Delete*",
                    "budgets:Modify*",
                    # CloudTrail administrative actions
                    "cloudtrail:CreateTrail",
                    "cloudtrail:DeleteTrail",
                    "cloudtrail:UpdateTrail",
                    "cloudtrail:StopLogging",
                    "cloudtrail:PutEventSelectors",
                    # Config administrative actions
                    "config:DeleteConfigRule",
                    "config:DeleteConfigurationRecorder",
                    "config:DeleteDeliveryChannel",
                    "config:StopConfigurationRecorder",
                    # GuardDuty administrative actions
                    "guardduty:DeleteDetector",
                    "guardduty:DeleteIPSet",
                    "guardduty:DeleteThreatIntelSet",
                    "guardduty:StopMonitoringMembers",
                    "guardduty:UpdateDetector",
                    # Security Hub administrative actions
                    "securityhub:DeleteInsight",
                    "securityhub:DisableSecurityHub",
                    "securityhub:UpdateSecurityHubConfiguration",
                    # KMS administrative actions
                    "kms:CreateKey",
                    "kms:DeleteKey",
                    "kms:ScheduleKeyDeletion",
                    "kms:CancelKeyDeletion",
                    "kms:CreateAlias",
                    "kms:DeleteAlias",
                    "kms:UpdateAlias",
                    "kms:CreateGrant",
                    "kms:RetireGrant",
                    "kms:RevokeGrant",
                    "kms:PutKeyPolicy",
                    # Prevent modification of this boundary policy
                    "iam:DeleteRolePermissionsBoundary",
                    "iam:PutRolePermissionsBoundary",
                ],
                "Resource": "*",
            },
            # Allow specific IAM actions only on partner-specific resources
            {
                "Effect": "Allow",
                "Action": ["iam:PassRole"],
                "Resource": [
                    f"arn:aws:iam::{account_id}:role/{partner_name.upper()}-*",
                    f"arn:aws:iam::{account_id}:role/service-role/{partner_name.upper()}-*",
                ],
            },
        ],
    }

    return boundary_policy


def get_basic_boundary_policy(account_id: str) -> Dict[str, Any]:
    """
    Get basic permission boundary policy with minimal permissions.

    Args:
        account_id: AWS account ID

    Returns:
        Dict: Basic IAM policy document for permission boundary
    """
    boundary_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:Describe*",
                    "ec2:Get*",
                    "s3:GetObject",
                    "s3:ListBucket",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "sts:GetCallerIdentity",
                ],
                "Resource": "*",
            },
            {
                "Effect": "Deny",
                "Action": ["iam:*", "organizations:*", "aws-portal:*"],
                "Resource": "*",
            },
        ],
    }

    return boundary_policy


def get_role_policies(partner_name: str, account_id: str) -> List[Dict[str, Any]]:
    """
    Get role policies for the partner assume role.

    Args:
        partner_name: Partner name
        account_id: AWS account ID

    Returns:
        List of IAM policy documents for the role
    """
    # Policy 1: Core services and EC2
    policy1 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    # EC2 core operations
                    "ec2:DescribeInstances",
                    "ec2:DescribeImages",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeVpcs",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeKeyPairs",
                    "ec2:DescribeInstanceTypes",
                    "ec2:DescribeAvailabilityZones",
                    "ec2:DescribeRegions",
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                    "ec2:StartInstances",
                    "ec2:StopInstances",
                    "ec2:RebootInstances",
                    "ec2:ModifyInstanceAttribute",
                    # Outposts - critical for telco lab
                    "outposts:GetOutpost",
                    "outposts:ListOutposts",
                    "outposts:GetOutpostInstanceTypes",
                    "outposts:ListSites",
                    "outposts:GetSite",
                    # EKS operations
                    "eks:CreateCluster",
                    "eks:DescribeCluster",
                    "eks:ListClusters",
                    "eks:UpdateCluster",
                    "eks:DeleteCluster",
                    "eks:CreateNodegroup",
                    "eks:DescribeNodegroup",
                    "eks:ListNodegroups",
                    "eks:UpdateNodegroupConfig",
                    "eks:DeleteNodegroup",
                    # IAM read operations
                    "iam:GetRole",
                    "iam:ListRoles",
                    "iam:GetInstanceProfile",
                    "iam:ListInstanceProfiles",
                    "iam:PassRole",
                ],
                "Resource": "*",
            }
        ],
    }

    # Policy 2: Advanced networking and storage
    policy2 = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    # S3 operations
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:CreateBucket",
                    "s3:DeleteBucket",
                    # CloudFormation
                    "cloudformation:CreateStack",
                    "cloudformation:UpdateStack",
                    "cloudformation:DeleteStack",
                    "cloudformation:DescribeStacks",
                    "cloudformation:ListStacks",
                    "cloudformation:GetTemplate",
                    "cloudformation:ValidateTemplate",
                    # CloudWatch and logging
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                    "cloudwatch:PutMetricData",
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:ListMetrics",
                    # Systems Manager
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:PutParameter",
                    "ssm:DeleteParameter",
                    "ssm:DescribeParameters",
                    "ssm:SendCommand",
                    "ssm:GetCommandInvocation",
                    # Secrets Manager
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:CreateSecret",
                    "secretsmanager:UpdateSecret",
                    "secretsmanager:DeleteSecret",
                ],
                "Resource": "*",
            }
        ],
    }

    return [policy1, policy2]
