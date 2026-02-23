# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Input validation utilities for TelcoCLI.

This module provides centralized input validation for security-critical operations.
All CLI commands should use these validators to prevent injection attacks and
ensure data integrity.
"""

import re
from typing import List, Optional, Tuple

from telco_cli.utils.constants import (
    ARN_LENGTH_MAX,
    DEFAULT_AWS_ACCOUNT_ID_LENGTH,
    DEFAULT_INPUT_MAX_LENGTH,
    DURATION_DAYS_MAX,
    DURATION_DAYS_MIN,
    DURATION_HOURS_MAX,
    DURATION_HOURS_MIN,
    DURATION_MINUTES_MAX,
    DURATION_MINUTES_MIN,
    INPUT_LENGTH_MAX,
    INPUT_LENGTH_MIN,
    PARTNER_NAME_MAX_LENGTH,
    PARTNER_NAME_MIN_LENGTH,
    PATTERN_AWS_ARN,
    PATTERN_DURATION,
    PATTERN_EMAIL,
    PATTERN_HOST_ID,
    PATTERN_OUTPOST_ID,
    PATTERN_PARTNER_NAME,
    PATTERN_RESOURCE_NAME,
    RESOURCE_NAME_LENGTH_MAX,
    SENSITIVE_PATTERNS,
)


def validate_aws_account_id(account_id: str) -> bool:
    """Validate AWS account ID format."""
    if not account_id:
        return False

    sanitized = re.sub(r"[^\d]", "", str(account_id))

    if len(sanitized) != DEFAULT_AWS_ACCOUNT_ID_LENGTH:
        return False

    return True


def validate_partner_name(partner_name: str) -> bool:
    """Validate partner name format."""
    if not partner_name:
        return False

    if len(partner_name) < PARTNER_NAME_MIN_LENGTH:
        return False

    if len(partner_name) > PARTNER_NAME_MAX_LENGTH:
        return False

    if not re.match(PATTERN_PARTNER_NAME, partner_name):
        return False

    return True


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address format."""
    if not email:
        return False, "Email address is required"

    if not re.match(PATTERN_EMAIL, email):
        return False, "Invalid email address format"

    return True, ""


def validate_duration(duration: str) -> Tuple[bool, str]:
    """Validate duration format (e.g., '30d', '2h', '45m')."""
    if not duration:
        return False, "Duration is required"

    match = re.match(PATTERN_DURATION, duration.lower())

    if not match:
        return False, "Duration must be in format like '30d', '2h', or '45m'"

    value, unit = match.groups()
    value = int(value)

    if unit == "d" and (value < DURATION_DAYS_MIN or value > DURATION_DAYS_MAX):
        return (
            False,
            f"Duration in days must be between {DURATION_DAYS_MIN} and {DURATION_DAYS_MAX}",
        )
    elif unit == "h" and (value < DURATION_HOURS_MIN or value > DURATION_HOURS_MAX):
        return (
            False,
            f"Duration in hours must be between {DURATION_HOURS_MIN} and {DURATION_HOURS_MAX}",
        )
    elif unit == "m" and (value < DURATION_MINUTES_MIN or value > DURATION_MINUTES_MAX):
        return (
            False,
            f"Duration in minutes must be between {DURATION_MINUTES_MIN} and {DURATION_MINUTES_MAX}",
        )

    return True, ""


def sanitize_input(input_str: str, max_length: int = DEFAULT_INPUT_MAX_LENGTH) -> str:
    """Sanitize user input for safe processing."""
    if not input_str:
        return ""

    # Remove control characters and limit length
    sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", input_str)
    return sanitized[:max_length].strip()


def validate_outpost_id(outpost_id: str) -> Tuple[bool, str]:
    """Validate AWS Outpost ID format."""
    if not outpost_id:
        return False, "Outpost ID is required"

    if not re.match(PATTERN_OUTPOST_ID, outpost_id):
        return False, "Invalid Outpost ID format (should be op-xxxxxxxxxxxxxxxxx)"

    return True, ""


def validate_host_id(host_id: str) -> Tuple[bool, str]:
    """Validate AWS Dedicated Host ID format."""
    if not host_id:
        return False, "Host ID is required"

    if not re.match(PATTERN_HOST_ID, host_id):
        return False, "Invalid Host ID format (should be h-xxxxxxxxxxxxxxxxx)"

    return True, ""


def validate_eks_cluster_name(cluster_name: str) -> Tuple[bool, str]:
    """Validate EKS cluster name format."""
    if not cluster_name:
        return False, "EKS cluster name is required"

    if len(cluster_name) > 100:
        return False, "EKS cluster name must be 100 characters or less"

    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\-_]*$", cluster_name):
        return (
            False,
            "EKS cluster name must start with alphanumeric and contain only letters, numbers, hyphens, and underscores",
        )

    return True, ""


def validate_cluster_name(cluster_name: str) -> Tuple[bool, str]:
    """Validate EKS cluster name format."""
    if not cluster_name:
        return False, "Cluster name is required"

    if len(cluster_name) < 1 or len(cluster_name) > 100:
        return False, "Cluster name must be between 1 and 100 characters"

    if not re.match(r"^[a-zA-Z0-9-]+$", cluster_name):
        return False, "Cluster name can only contain letters, numbers, and hyphens"

    return True, ""


def validate_kubernetes_version(version: str) -> Tuple[bool, str]:
    """Validate Kubernetes version format."""
    if not version:
        return False, "Kubernetes version is required"

    if not re.match(r"^1\.\d{2}$", version):
        return False, "Kubernetes version must be in format 1.XX (e.g., 1.28)"

    return True, ""


def validate_vpc_cidr(cidr: str) -> Tuple[bool, str]:
    """Validate VPC CIDR format."""
    if not cidr:
        return False, "VPC CIDR is required"

    cidr_pattern = r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
    if not re.match(cidr_pattern, cidr):
        return False, "Invalid CIDR format (should be like 10.0.0.0/16)"

    return True, ""


def validate_aws_arn(arn: str, allowed_services: Optional[List[str]] = None) -> Tuple[bool, str]:
    """
    Validate AWS ARN format.

    Args:
        arn: The ARN string to validate
        allowed_services: Optional list of allowed AWS service names (e.g., ['iam', 's3'])

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> validate_aws_arn("arn:aws:iam::123456789012:role/MyRole")
        (True, "")
        >>> validate_aws_arn("invalid-arn")
        (False, "Invalid ARN format")
    """
    if not arn:
        return False, "ARN is required"

    if len(arn) > ARN_LENGTH_MAX:
        return False, f"ARN exceeds maximum length of {ARN_LENGTH_MAX} characters"

    match = re.match(PATTERN_AWS_ARN, arn)
    if not match:
        return (
            False,
            "Invalid ARN format (expected: arn:partition:service:region:account-id:resource)",
        )

    # Extract service from ARN
    service = match.group(2)

    # Validate against allowed services if specified
    if allowed_services and service not in allowed_services:
        return False, f"Service '{service}' not in allowed services: {allowed_services}"

    return True, ""


def validate_resource_name(
    name: str,
    resource_type: str = "resource",
    min_length: int = INPUT_LENGTH_MIN,
    max_length: int = RESOURCE_NAME_LENGTH_MAX,
) -> Tuple[bool, str]:
    """
    Validate AWS resource name format.

    Resource names must:
    - Start and end with alphanumeric characters
    - Contain only letters, numbers, hyphens, underscores, and periods
    - Be within length limits

    Args:
        name: The resource name to validate
        resource_type: Type of resource for error messages (e.g., 'role', 'bucket')
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, f"{resource_type.capitalize()} name is required"

    if len(name) < min_length:
        return False, f"{resource_type.capitalize()} name must be at least {min_length} characters"

    if len(name) > max_length:
        return (
            False,
            f"{resource_type.capitalize()} name exceeds maximum length of {max_length} characters",
        )

    if not re.match(PATTERN_RESOURCE_NAME, name):
        return (
            False,
            f"{resource_type.capitalize()} name must start and end with alphanumeric characters "
            "and contain only letters, numbers, hyphens, underscores, and periods",
        )

    return True, ""


def validate_input_length(
    input_str: str,
    field_name: str = "Input",
    min_length: int = INPUT_LENGTH_MIN,
    max_length: int = INPUT_LENGTH_MAX,
) -> Tuple[bool, str]:
    """
    Validate input string length.

    Args:
        input_str: The input string to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length (default: 1)
        max_length: Maximum allowed length (default: 10000)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if input_str is None:
        return False, f"{field_name} is required"

    length = len(input_str)

    if length < min_length:
        return False, f"{field_name} must be at least {min_length} characters"

    if length > max_length:
        return False, f"{field_name} exceeds maximum length of {max_length} characters"

    return True, ""


def sanitize_for_logging(text: str, replacement: str = "[REDACTED]") -> str:
    """
    Sanitize text for safe logging by removing sensitive data patterns.

    This function removes or masks:
    - Passwords and secrets
    - API keys and tokens
    - AWS access keys
    - Other sensitive patterns

    Args:
        text: The text to sanitize
        replacement: String to replace sensitive data with

    Returns:
        Sanitized text safe for logging

    Example:
        >>> sanitize_for_logging("password=secret123")
        "password=[REDACTED]"
        >>> sanitize_for_logging("AKIAIOSFODNN7EXAMPLE")
        "[REDACTED]"
    """
    if not text:
        return ""

    sanitized = text

    for pattern in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized


def validate_aws_region(region: str) -> Tuple[bool, str]:
    """
    Validate AWS region format.

    Args:
        region: The AWS region to validate (e.g., 'us-east-1', 'eu-west-2')

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not region:
        return False, "AWS region is required"

    # AWS region pattern: xx-xxxx-N or xx-xxx-N
    region_pattern = r"^[a-z]{2}-[a-z]+-\d{1,2}$"
    if not re.match(region_pattern, region):
        return False, "Invalid AWS region format (expected: us-east-1, eu-west-2, etc.)"

    return True, ""


def validate_s3_bucket_name(bucket_name: str) -> Tuple[bool, str]:
    """
    Validate S3 bucket name according to AWS naming rules.

    S3 bucket names must:
    - Be between 3 and 63 characters long
    - Consist only of lowercase letters, numbers, hyphens, and periods
    - Begin and end with a letter or number
    - Not contain consecutive periods
    - Not be formatted as an IP address

    Args:
        bucket_name: The S3 bucket name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not bucket_name:
        return False, "S3 bucket name is required"

    if len(bucket_name) < 3:
        return False, "S3 bucket name must be at least 3 characters"

    if len(bucket_name) > 63:
        return False, "S3 bucket name must be 63 characters or less"

    # Must be lowercase
    if bucket_name != bucket_name.lower():
        return False, "S3 bucket name must be lowercase"

    # Must start and end with letter or number
    if not re.match(r"^[a-z0-9].*[a-z0-9]$|^[a-z0-9]$", bucket_name):
        return False, "S3 bucket name must start and end with a letter or number"

    # Only allowed characters
    if not re.match(r"^[a-z0-9.-]+$", bucket_name):
        return (
            False,
            "S3 bucket name can only contain lowercase letters, numbers, hyphens, and periods",
        )

    # No consecutive periods
    if ".." in bucket_name:
        return False, "S3 bucket name cannot contain consecutive periods"

    # Not IP address format
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", bucket_name):
        return False, "S3 bucket name cannot be formatted as an IP address"

    return True, ""


def validate_iam_role_name(role_name: str) -> Tuple[bool, str]:
    """
    Validate IAM role name according to AWS naming rules.

    IAM role names must:
    - Be between 1 and 64 characters
    - Contain only alphanumeric characters, plus (+), equals (=), comma (,),
      period (.), at (@), underscore (_), and hyphen (-)

    Args:
        role_name: The IAM role name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not role_name:
        return False, "IAM role name is required"

    if len(role_name) > 64:
        return False, "IAM role name must be 64 characters or less"

    # IAM role name pattern
    if not re.match(r"^[\w+=,.@-]+$", role_name):
        return (
            False,
            "IAM role name can only contain alphanumeric characters, "
            "plus (+), equals (=), comma (,), period (.), at (@), underscore (_), and hyphen (-)",
        )

    return True, ""
