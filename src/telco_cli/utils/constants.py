# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Constants for TelcoCLI."""

import logging

# Program info
PROG_NAME = "telcocli"
PROG_VERSION = "telcocli 1.0.0"
PROG_DESCRIPTION = "AWS Telco CLI - Command line tools for AWS Telco operations"

# Argument names
ARG_VERSION = "--version"
ARG_VERBOSE = "--verbose"
ARG_VERBOSE_SHORT = "-v"
ARG_QUIET = "--quiet"
ARG_QUIET_SHORT = "-q"
ARG_LOG_FILE = "--log-file"
ARG_COMMAND = "command"

# Argument actions
ACTION_VERSION = "version"
ACTION_STORE_TRUE = "store_true"

# Argument help messages
HELP_VERBOSE = "Enable verbose logging (debug level)"
HELP_QUIET = "Suppress informational messages (only show warnings/errors)"
HELP_LOG_FILE = "Write logs to specified file"
HELP_COMMANDS = "Available commands"

# Error messages
ERROR_NO_COMMANDS = "❌ [red]Error: No commands found![/red]"
ERROR_VERBOSE_QUIET_CONFLICT = "❌ [red]Error: Cannot use --verbose and --quiet together[/red]"
ERROR_UNEXPECTED = "❌ [red]Unexpected error: {error}[/red]"

# Warning messages
WARNING_CANCELLED = "\n⚠️  [yellow]Operation cancelled by user.[/yellow]"
WARNING_IMPORT_FAILED = "Could not import command module {module}: {error}"

# Log messages
LOG_CLI_STARTED = "TelcoCLI started with command: {command}"
LOG_ARGUMENTS = "Arguments: {args}"
LOG_EXECUTING_COMMAND = "Executing command: {command}"
LOG_CANCELLED = "Operation cancelled by user"
LOG_UNEXPECTED_ERROR = "Unexpected error occurred"

# Logging levels
LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING

# Logging level mapping
LOG_LEVEL_MAP = {
    "verbose": LOG_LEVEL_DEBUG,
    "quiet": LOG_LEVEL_WARNING,
    "default": LOG_LEVEL_INFO,
}

# Output Formats
OUTPUT_FORMAT_JSON = "json"
OUTPUT_FORMAT_TABLE = "table"
OUTPUT_FORMAT_SUMMARY = "summary"
OUTPUT_FORMAT_TEXT = "text"

OUTPUT_FORMATS = [
    OUTPUT_FORMAT_JSON,
    OUTPUT_FORMAT_TABLE,
    OUTPUT_FORMAT_SUMMARY,
    OUTPUT_FORMAT_TEXT,
]

# AWS Services
AWS_SERVICE_ORGANIZATIONS = "organizations"
AWS_SERVICE_STS = "sts"
AWS_SERVICE_IAM = "iam"
AWS_SERVICE_EC2 = "ec2"

# AWS Error Codes
AWS_ERROR_ORGANIZATIONS_NOT_IN_USE = "AWSOrganizationsNotInUseException"
AWS_ERROR_ACCESS_DENIED = "AccessDenied"
AWS_ERROR_ACCOUNT_NOT_FOUND = "AccountNotFoundException"
AWS_ERROR_NO_SUCH_ENTITY = "NoSuchEntity"

# Health Check Status
HEALTH_STATUS_HEALTHY = "healthy"
HEALTH_STATUS_UNHEALTHY = "unhealthy"

# Default Values
DEFAULT_MAX_SESSION_DURATION = 3600
DEFAULT_INPUT_MAX_LENGTH = 256
DEFAULT_AWS_ACCOUNT_ID_LENGTH = 12

# Validation Patterns
PATTERN_AWS_ACCOUNT_ID = r"^\d{12}$"
PATTERN_PARTNER_NAME = r"^[a-zA-Z][a-zA-Z0-9\-_]*$"
PATTERN_EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
PATTERN_DURATION = r"^(\d+)([dhm])$"
PATTERN_OUTPOST_ID = r"^op-[a-f0-9]{17}$"
PATTERN_HOST_ID = r"^h-[a-f0-9]{17}$"

# AWS ARN Pattern - matches standard ARN format
# arn:partition:service:region:account-id:resource-type/resource-id
PATTERN_AWS_ARN = r"^arn:(aws|aws-cn|aws-us-gov):([a-zA-Z0-9-]+):([a-z0-9-]*):(\d{12}|):(.+)$"

# Resource Name Pattern - alphanumeric with hyphens, underscores, periods
PATTERN_RESOURCE_NAME = r"^[a-zA-Z0-9][a-zA-Z0-9\-_.]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$"

# Input Length Limits
INPUT_LENGTH_MIN = 1
INPUT_LENGTH_MAX = 10000
ARN_LENGTH_MAX = 2048
RESOURCE_NAME_LENGTH_MAX = 256

# Sensitive Data Patterns for Log Sanitization
SENSITIVE_PATTERNS = [
    r"(?i)(password|passwd|pwd)\s*[=:]\s*\S+",
    r"(?i)(secret|api[_-]?key|access[_-]?key)\s*[=:]\s*\S+",
    r"(?i)(token|bearer)\s*[=:]\s*\S+",
    r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
    r"(?i)aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*\S+",
]

# Duration Limits
DURATION_DAYS_MIN = 1
DURATION_DAYS_MAX = 365
DURATION_HOURS_MIN = 1
DURATION_HOURS_MAX = 8760
DURATION_MINUTES_MIN = 1
DURATION_MINUTES_MAX = 525600

# Partner Name Limits
PARTNER_NAME_MIN_LENGTH = 2
PARTNER_NAME_MAX_LENGTH = 32
