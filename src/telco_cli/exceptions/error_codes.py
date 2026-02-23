# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Error code definitions for the Telco CLI."""

from enum import IntEnum


class ErrorCode(IntEnum):
    """Error codes that map to exit codes."""

    # Success
    SUCCESS = 0

    # Generic/unknown error
    UNKNOWN_ERROR = 1

    # Validation errors (exit code 2)
    VALIDATION_ERROR = 2
    INVALID_PARTNER_NAME = 2
    INVALID_SUBNET = 2
    INVALID_DURATION = 2

    # AWS errors (exit code 3)
    AWS_CONNECTION_ERROR = 3
    AWS_CREDENTIALS_MISSING = 3
    AWS_CREDENTIALS_INVALID = 3
    AWS_SERVICE_ERROR = 3

    # Server discovery errors (exit code 4)
    SERVER_DISCOVERY_ERROR = 4
    NO_VPN_SERVER_FOUND = 4

    # SSM errors (exit code 5)
    SSM_CONNECTION_ERROR = 5
    SSM_AGENT_OFFLINE = 5

    # Command execution errors (exit code 6)
    COMMAND_EXECUTION_ERROR = 6
    COMMAND_TIMEOUT = 6

    # File operation errors (exit code 7)
    FILE_OPERATION_ERROR = 7
    FILE_WRITE_ERROR = 7
    FILE_VERIFICATION_ERROR = 7

    # Certificate errors (exit code 8)
    CERTIFICATE_ERROR = 8
    CERTIFICATE_NOT_FOUND = 8
    CERTIFICATE_GENERATION_FAILED = 8

    # Configuration errors (exit code 9)
    CONFIGURATION_ERROR = 9
    ROUTING_CONFIG_ERROR = 9

    # AWS Organizations specific errors (exit code 10)
    ORGANIZATIONS_NOT_ENABLED = 10
    ORGANIZATIONS_ACCESS_DENIED = 10
    PARTNER_CREATION_FAILED = 10

    # User interaction errors (exit code 11)
    USER_CANCELLED = 11

    # AWS API errors (exit code 12)
    AWS_API_ERROR = 12
    AWS_CLIENT_INIT_FAILED = 12

    # Credential errors (exit code 13)
    CREDENTIAL_PARSE_ERROR = 13
    MISSING_CREDENTIALS = 13

    # Health check errors (exit code 14)
    HEALTH_CHECK_FAILED = 14

    # Host management errors (exit code 15)
    HOST_RELEASE_FAILED = 15

    # Partner management errors (exit code 16)
    PARTNER_LISTING_FAILED = 16
    PARTNER_NOT_FOUND = 16

    # EKS cluster errors (exit code 17)
    EKS_CLUSTER_DEPLOYMENT_FAILED = 17
    EKS_DEPLOYMENT_FAILED = 17
    EKS_CLUSTER_NOT_FOUND = 17
    EKS_WORKER_JOIN_FAILED = 17
    EKS_CLUSTER_DELETE_FAILED = 17
    TEMPLATE_NOT_FOUND = 17

    # JDA account errors (exit code 18)
    JDA_ACCOUNT_SETUP_FAILED = 18
    JDA_CREDENTIALS_EXPIRED = 18
    JDA_ROLE_ASSUMPTION_FAILED = 18
    CLOUDFORMATION_STACK_FAILED = 18
    CLOUDFORMATION_TEMPLATE_INVALID = 18

    # kubectl errors (exit code 19)
    KUBECTL_CONFIG_FAILED = 19
    KUBECTL_ACCESS_DENIED = 19
    KUBECONFIG_GENERATION_FAILED = 19

    # JDA credential errors (exit code 20)
    JDA_CREDENTIAL_GENERATION_FAILED = 20
    JDA_ACCOUNT_ACCESS_DENIED = 20

    # Template and validation errors (exit code 21)
    INVALID_PARAMETER = 21
    VALIDATION_FAILED = 21
