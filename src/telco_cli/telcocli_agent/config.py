# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Centralized configuration for TelcoCLI agent."""

import os

# Model Configuration
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
DEFAULT_REGION = "us-east-1"
FALLBACK_REGIONS = ["us-east-1", "us-west-2"]

# Bedrock Configuration
BEDROCK_REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]

# Credential Error Indicators
CREDENTIAL_ERROR_INDICATORS = [
    "ExpiredToken",
    "ExpiredTokenException",
    "security token included in the request is expired",
    "InvalidUserID.NotFound",
    "SignatureDoesNotMatch",
    "InvalidAccessKeyId",
    "TokenRefreshRequired",
    "CredentialsNotFound",
    "UnauthorizedOperation",
]


def get_aws_region() -> str:
    """Get AWS region from environment or default."""
    return os.environ.get("AWS_DEFAULT_REGION", DEFAULT_REGION)


def get_aws_profile() -> str:
    """Get AWS profile from environment or default."""
    return os.environ.get("AWS_PROFILE", "default")


def is_credential_error(error_msg: str) -> bool:
    """Check if error is credential-related."""
    return any(indicator in error_msg for indicator in CREDENTIAL_ERROR_INDICATORS)
