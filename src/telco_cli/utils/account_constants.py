# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Constants specific to AWS account management operations."""

# AWS Account Types
ACCOUNT_TYPE_MANAGEMENT = "management"
ACCOUNT_TYPE_SECURITY = "security"
ACCOUNT_TYPE_PARTNER = "partner"
ACCOUNT_TYPE_LEGACY = "legacy"

ACCOUNT_TYPES = [
    ACCOUNT_TYPE_MANAGEMENT,
    ACCOUNT_TYPE_SECURITY,
    ACCOUNT_TYPE_PARTNER,
    ACCOUNT_TYPE_LEGACY,
]

# AWS Account Status
ACCOUNT_STATUS_ACTIVE = "ACTIVE"
ACCOUNT_STATUS_SUSPENDED = "SUSPENDED"
ACCOUNT_STATUS_PENDING_CLOSURE = "PENDING_CLOSURE"

ACCOUNT_STATUSES = [
    ACCOUNT_STATUS_ACTIVE,
    ACCOUNT_STATUS_SUSPENDED,
    ACCOUNT_STATUS_PENDING_CLOSURE,
]

# Account Type Detection Keywords
MANAGEMENT_KEYWORDS = ["management"]
SECURITY_KEYWORDS = ["log archive", "audit", "security"]
PARTNER_KEYWORDS = ["aws-5gc-pmt"]
LEGACY_KEYWORDS = ["csectl-", "csectl"]

# Account Type Detection Tags
MANAGEMENT_TAGS = {"AccountType": "management"}
PARTNER_TAGS = {
    "ManagedBy": ["awstelco", "telcocli"],
    "Partner": None,  # Any value
}

# AWS Organizations Constants
OU_PREFIX = "ou-"
ROOT_OU_NAME = "Root"
UNKNOWN_OU = {"Id": "Unknown", "Name": "Unknown"}

# Default Role Names
DEFAULT_CROSS_ACCOUNT_ROLE = "OrganizationAccountAccessRole"
TELCO_CROSS_ACCOUNT_ROLE_PREFIX = "TelcoPartnerRole"

# Account Limits and Defaults
MAX_ACCOUNT_NAME_LENGTH = 50
MAX_EMAIL_LENGTH = 64
DEFAULT_AWS_ACCOUNT_ID_LENGTH = 12

# Account Creation Constants
EXTERNAL_ID_PREFIX = "telco-"
TRUST_POLICY_VERSION = "2012-10-17"

# Summary Display Limits
MAX_OU_DISPLAY_COUNT = 10
