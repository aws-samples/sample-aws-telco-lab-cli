"""Tests for AWS utilities.

Note: All AWS account IDs and resource IDs in this test file are example/mock values.
These are test fixtures and do not represent real AWS resources.
"""

import json
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

from telco_cli.utils.aws_utils import (
    AWSClientManager,
    EC2Helper,
    IAMHelper,
    OrganizationsHelper,
    check_aws_permissions,
    format_aws_error,
    get_caller_identity,
    validate_aws_account_id,
)


class TestAWSClientManager:
    """Test cases for AWSClientManager."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        manager = AWSClientManager()
        assert manager.profile is None
        assert manager.region is None
        assert manager._session is None
        assert manager._clients == {}

    def test_init_with_parameters(self):
        """Test initialization with custom parameters."""
        manager = AWSClientManager(profile="test-profile", region="us-west-2")
        assert manager.profile == "test-profile"
        assert manager.region == "us-west-2"

    @patch("telco_cli.utils.aws_utils.boto3.Session")
    def test_get_session_success(self, mock_session_class):
        """Test successful session creation."""
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_session.client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.return_value = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/test",
        }
        mock_session_class.return_value = mock_session

        manager = AWSClientManager(profile="test-profile", region="us-west-2")
        session = manager.get_session()

        assert session == mock_session
        mock_session_class.assert_called_once_with(
            profile_name="test-profile", region_name="us-west-2"
        )
        mock_sts_client.get_caller_identity.assert_called_once()

    @patch("telco_cli.utils.aws_utils.boto3.Session")
    def test_get_session_no_credentials_error(self, mock_session_class):
        """Test session creation with no credentials error."""
        mock_session_class.side_effect = NoCredentialsError()

        manager = AWSClientManager()
        with pytest.raises(ValueError) as exc_info:
            manager.get_session()

        assert "AWS credentials error" in str(exc_info.value)

    @patch("telco_cli.utils.aws_utils.boto3.Session")
    def test_get_session_profile_not_found(self, mock_session_class):
        """Test session creation with profile not found error."""
        mock_session_class.side_effect = ProfileNotFound(profile="test-profile")

        manager = AWSClientManager(profile="test-profile")
        with pytest.raises(ValueError) as exc_info:
            manager.get_session()

        assert "AWS credentials error" in str(exc_info.value)

    @patch("telco_cli.utils.aws_utils.boto3.Session")
    def test_get_session_client_error(self, mock_session_class):
        """Test session creation with client error."""
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_session.client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "GetCallerIdentity"
        )
        mock_session_class.return_value = mock_session

        manager = AWSClientManager()
        with pytest.raises(ValueError) as exc_info:
            manager.get_session()

        assert "AWS session error" in str(exc_info.value)

    @patch("telco_cli.utils.aws_utils.boto3.Session")
    def test_get_client(self, mock_session_class):
        """Test getting AWS service client."""
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client.return_value = mock_client
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        # Mock different clients for different services
        def mock_client_factory(service_name):
            if service_name == "sts":
                return mock_sts_client
            return mock_client

        mock_session.client.side_effect = mock_client_factory
        mock_session_class.return_value = mock_session

        manager = AWSClientManager()
        client = manager.get_client("ec2")

        assert client == mock_client
        assert manager._clients["ec2"] == mock_client

    @patch("telco_cli.utils.aws_utils.boto3.Session")
    def test_get_client_cached(self, mock_session_class):
        """Test that clients are cached."""
        mock_session = Mock()
        mock_client = Mock()
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

        def mock_client_factory(service_name):
            if service_name == "sts":
                return mock_sts_client
            return mock_client

        mock_session.client.side_effect = mock_client_factory
        mock_session_class.return_value = mock_session

        manager = AWSClientManager()
        client1 = manager.get_client("ec2")
        client2 = manager.get_client("ec2")

        assert client1 == client2
        assert mock_session.client.call_count == 2  # Once for STS, once for EC2


class TestOrganizationsHelper:
    """Test cases for OrganizationsHelper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client_manager = Mock()
        self.mock_org_client = Mock()
        self.mock_client_manager.get_client.return_value = self.mock_org_client
        self.helper = OrganizationsHelper(self.mock_client_manager)

    def test_create_account_success(self):
        """Test successful account creation."""
        expected_response = {
            "CreateAccountStatus": {
                "Id": "car-123456789012",
                "AccountName": "Test Account",
                "State": "IN_PROGRESS",
            }
        }
        self.mock_org_client.create_account.return_value = expected_response

        result = self.helper.create_account("Test Account", "test@example.com")

        assert result == expected_response
        self.mock_org_client.create_account.assert_called_once_with(
            AccountName="Test Account",
            Email="test@example.com",
            RoleName="OrganizationAccountAccessRole",
        )

    def test_create_account_with_custom_role(self):
        """Test account creation with custom role name."""
        expected_response = {"CreateAccountStatus": {"Id": "car-123456789012"}}
        self.mock_org_client.create_account.return_value = expected_response

        self.helper.create_account("Test Account", "test@example.com", "CustomRole")

        self.mock_org_client.create_account.assert_called_once_with(
            AccountName="Test Account", Email="test@example.com", RoleName="CustomRole"
        )

    def test_create_account_client_error(self):
        """Test account creation with client error."""
        self.mock_org_client.create_account.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "Invalid email"}},
            "CreateAccount",
        )

        with pytest.raises(ValueError) as exc_info:
            self.helper.create_account("Test Account", "invalid-email")

        assert "Failed to create account" in str(exc_info.value)
        assert "InvalidParameterException" in str(exc_info.value)

    def test_describe_account_success(self):
        """Test successful account description."""
        expected_account = {
            "Id": "123456789012",
            "Name": "Test Account",
            "Email": "test@example.com",
            "Status": "ACTIVE",
        }
        self.mock_org_client.describe_account.return_value = {"Account": expected_account}

        result = self.helper.describe_account("123456789012")

        assert result == expected_account
        self.mock_org_client.describe_account.assert_called_once_with(AccountId="123456789012")

    def test_describe_account_not_found(self):
        """Test account description with account not found."""
        self.mock_org_client.describe_account.side_effect = ClientError(
            {"Error": {"Code": "AccountNotFoundException", "Message": "Account not found"}},
            "DescribeAccount",
        )

        with pytest.raises(ValueError) as exc_info:
            self.helper.describe_account("123456789012")

        assert "Account 123456789012 not found in organization" in str(exc_info.value)

    def test_list_accounts_success(self):
        """Test successful account listing."""
        expected_accounts = [
            {"Id": "123456789012", "Name": "Account 1"},
            {"Id": "123456789013", "Name": "Account 2"},
        ]

        mock_paginator = Mock()
        mock_paginator.paginate.return_value = [{"Accounts": expected_accounts}]
        self.mock_org_client.get_paginator.return_value = mock_paginator

        result = self.helper.list_accounts()

        assert result == expected_accounts
        self.mock_org_client.get_paginator.assert_called_once_with("list_accounts")


class TestIAMHelper:
    """Test cases for IAMHelper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client_manager = Mock()
        self.mock_iam_client = Mock()
        self.mock_client_manager.get_client.return_value = self.mock_iam_client
        self.helper = IAMHelper(self.mock_client_manager)

    def test_create_cross_account_role_success(self):
        """Test successful cross-account role creation."""
        expected_role = {"RoleName": "TestRole", "Arn": "arn:aws:iam::123456789012:role/TestRole"}
        self.mock_iam_client.create_role.return_value = {"Role": expected_role}

        result = self.helper.create_cross_account_role("TestRole", "123456789013")

        assert result == expected_role
        self.mock_iam_client.create_role.assert_called_once()

        # Verify the trust policy structure
        call_args = self.mock_iam_client.create_role.call_args
        trust_policy = json.loads(call_args[1]["AssumeRolePolicyDocument"])
        assert trust_policy["Version"] == "2012-10-17"
        assert "123456789013" in trust_policy["Statement"][0]["Principal"]["AWS"]

    def test_create_cross_account_role_with_policies(self):
        """Test cross-account role creation with policy attachments."""
        expected_role = {"RoleName": "TestRole"}
        self.mock_iam_client.create_role.return_value = {"Role": expected_role}

        policy_arns = ["arn:aws:iam::aws:policy/ReadOnlyAccess"]
        self.helper.create_cross_account_role("TestRole", "123456789013", policy_arns)

        self.mock_iam_client.attach_role_policy.assert_called_once_with(
            RoleName="TestRole", PolicyArn="arn:aws:iam::aws:policy/ReadOnlyAccess"
        )

    def test_delete_role_success(self):
        """Test successful role deletion."""
        # Mock attached policies
        self.mock_iam_client.list_attached_role_policies.return_value = {
            "AttachedPolicies": [{"PolicyArn": "arn:aws:iam::aws:policy/ReadOnlyAccess"}]
        }

        # Mock inline policies
        self.mock_iam_client.list_role_policies.return_value = {"PolicyNames": ["InlinePolicy1"]}

        self.helper.delete_role("TestRole")

        # Verify detach, delete inline policy, and delete role calls
        self.mock_iam_client.detach_role_policy.assert_called_once()
        self.mock_iam_client.delete_role_policy.assert_called_once()
        self.mock_iam_client.delete_role.assert_called_once_with(RoleName="TestRole")

    def test_delete_role_not_found(self):
        """Test role deletion when role doesn't exist."""
        self.mock_iam_client.list_attached_role_policies.side_effect = ClientError(
            {"Error": {"Code": "NoSuchEntity", "Message": "Role not found"}},
            "ListAttachedRolePolicies",
        )

        # Should not raise exception for NoSuchEntity
        self.helper.delete_role("NonExistentRole")


class TestEC2Helper:
    """Test cases for EC2Helper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client_manager = Mock()
        self.mock_ec2_client = Mock()
        self.mock_client_manager.get_client.return_value = self.mock_ec2_client
        self.helper = EC2Helper(self.mock_client_manager)

    def test_describe_dedicated_hosts_success(self):
        """Test successful dedicated hosts description."""
        expected_hosts = [
            {"HostId": "h-1234567890abcdef0", "State": "available"},
            {"HostId": "h-1234567890abcdef1", "State": "available"},
        ]
        self.mock_ec2_client.describe_hosts.return_value = {"Hosts": expected_hosts}

        result = self.helper.describe_dedicated_hosts()

        assert result == expected_hosts
        self.mock_ec2_client.describe_hosts.assert_called_once_with()

    def test_describe_dedicated_hosts_with_ids(self):
        """Test dedicated hosts description with specific host IDs."""
        host_ids = ["h-1234567890abcdef0"]
        expected_hosts = [{"HostId": "h-1234567890abcdef0", "State": "available"}]
        self.mock_ec2_client.describe_hosts.return_value = {"Hosts": expected_hosts}

        result = self.helper.describe_dedicated_hosts(host_ids)

        assert result == expected_hosts
        self.mock_ec2_client.describe_hosts.assert_called_once_with(HostIds=host_ids)

    def test_allocate_hosts_success(self):
        """Test successful host allocation."""
        expected_host_ids = ["h-1234567890abcdef0", "h-1234567890abcdef1"]
        self.mock_ec2_client.allocate_hosts.return_value = {"HostIds": expected_host_ids}

        result = self.helper.allocate_hosts("m5.large", 2, "us-west-2a")

        assert result == expected_host_ids
        self.mock_ec2_client.allocate_hosts.assert_called_once_with(
            InstanceType="m5.large", Quantity=2, AvailabilityZone="us-west-2a"
        )

    def test_release_hosts_success(self):
        """Test successful host release."""
        host_ids = ["h-1234567890abcdef0", "h-1234567890abcdef1"]

        self.helper.release_hosts(host_ids)

        self.mock_ec2_client.release_hosts.assert_called_once_with(HostIds=host_ids)


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_validate_aws_account_id_valid(self):
        """Test validation of valid AWS account ID."""
        assert validate_aws_account_id("123456789012") is True

    def test_validate_aws_account_id_invalid(self):
        """Test validation of invalid AWS account ID."""
        assert validate_aws_account_id("12345") is False
        assert validate_aws_account_id("1234567890123") is False
        assert validate_aws_account_id("abcdefghijkl") is False

    def test_format_aws_error(self):
        """Test formatting of AWS ClientError."""
        error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied to resource"}},
            "TestOperation",
        )

        result = format_aws_error(error)

        assert "AccessDenied" in result
        assert "Access denied to resource" in result

    def test_format_aws_error_with_special_characters(self):
        """Test formatting of AWS error with special characters."""
        error = ClientError(
            {
                "Error": {
                    "Code": "InvalidInput",
                    "Message": "Invalid input: <script>alert('xss')</script>",
                }
            },
            "TestOperation",
        )

        result = format_aws_error(error)

        # Should escape HTML characters
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    @patch("telco_cli.utils.aws_utils.AWSClientManager")
    def test_get_caller_identity_success(self, mock_manager_class):
        """Test successful caller identity retrieval."""
        mock_manager = Mock()
        mock_sts_client = Mock()
        mock_manager.get_client.return_value = mock_sts_client
        expected_identity = {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/test",
        }
        mock_sts_client.get_caller_identity.return_value = expected_identity

        result = get_caller_identity(mock_manager)

        assert result == expected_identity
        mock_manager.get_client.assert_called_once_with("sts")

    @patch("telco_cli.utils.aws_utils.AWSClientManager")
    def test_get_caller_identity_error(self, mock_manager_class):
        """Test caller identity retrieval with error."""
        mock_manager = Mock()
        mock_sts_client = Mock()
        mock_manager.get_client.return_value = mock_sts_client
        mock_sts_client.get_caller_identity.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "GetCallerIdentity"
        )

        with pytest.raises(ValueError) as exc_info:
            get_caller_identity(mock_manager)

        assert "Failed to get caller identity" in str(exc_info.value)

    def test_check_aws_permissions(self):
        """Test AWS permissions checking."""
        mock_manager = Mock()
        permissions = ["organizations:ListAccounts", "iam:GetRole"]

        result = check_aws_permissions(mock_manager, permissions)

        # Current implementation assumes all permissions are available
        assert result == {"organizations:ListAccounts": True, "iam:GetRole": True}
