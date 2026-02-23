"""Unit tests for account provisioning service."""

from unittest.mock import Mock, patch

import pytest

from telco_cli.services.account_provisioning import AccountProvisioningEngine


class TestAccountProvisioningEngine:
    """Test cases for AccountProvisioningEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = AccountProvisioningEngine()

    @patch("boto3.client")
    def test_assume_role_same_account_validation(self, mock_boto_client):
        """Test that assuming role in same account is properly blocked."""
        # Setup mocks
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
        self.engine.sts_client = mock_sts_client

        # Test: Should raise exception when trying to assume role in same account
        with pytest.raises(Exception) as exc_info:
            self.engine._assume_role_in_target_account("123456789012")

        assert "Cannot assume role in same account" in str(exc_info.value)
        assert "123456789012" in str(exc_info.value)

    @patch("boto3.client")
    def test_assume_role_different_account_success(self, mock_boto_client):
        """Test successful role assumption in different account."""
        # Setup mocks
        mock_sts_client = Mock()
        mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
        mock_sts_client.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "test-key",
                "SecretAccessKey": "test-secret",
                "SessionToken": "test-token",
            }
        }
        self.engine.sts_client = mock_sts_client

        # Test: Should succeed when assuming role in different account
        result = self.engine._assume_role_in_target_account("987654321098")

        assert result["AccessKeyId"] == "test-key"
        assert result["SecretAccessKey"] == "test-secret"
        assert result["SessionToken"] == "test-token"

        # Verify assume_role was called with correct parameters
        mock_sts_client.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::987654321098:role/OrganizationAccountAccessRole",
            RoleSessionName="telcocli-partner-setup",
        )
