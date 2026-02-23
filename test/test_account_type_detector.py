"""Tests for account type detector.

Note: All AWS account IDs in this test file are example/mock values.
These are test fixtures and do not represent real AWS resources.
"""

from telco_cli.utils.account_constants import (
    ACCOUNT_TYPE_LEGACY,
    ACCOUNT_TYPE_MANAGEMENT,
    ACCOUNT_TYPE_PARTNER,
    ACCOUNT_TYPE_SECURITY,
)
from telco_cli.utils.account_type_detector import AccountTypeDetector


class TestAccountTypeDetector:
    """Test cases for AccountTypeDetector."""

    def test_determine_management_account_by_name(self):
        """Test detection of management account by name."""
        account = {"Name": "Management Account", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_MANAGEMENT

    def test_determine_management_account_by_tag(self):
        """Test detection of management account by tag."""
        account = {"Name": "Some Account", "Id": "123456789012"}
        tags = {"AccountType": "management"}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_MANAGEMENT

    def test_determine_security_account_by_exact_name(self):
        """Test detection of security account by exact name match."""
        test_cases = [
            {"Name": "Log Archive", "Id": "123456789012"},
            {"Name": "Audit", "Id": "123456789012"},
        ]

        for account in test_cases:
            tags = {}
            result = AccountTypeDetector.determine_account_type(account, tags)
            assert result == ACCOUNT_TYPE_SECURITY, f"Account {account['Name']} should be security"

    def test_determine_security_account_by_keyword(self):
        """Test detection of security account by keyword in name."""
        account = {"Name": "Security Operations Account", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_SECURITY

    def test_determine_partner_account_by_managed_by_tag(self):
        """Test detection of partner account by ManagedBy tag."""
        test_cases = [
            {"ManagedBy": "awstelco"},
            {"ManagedBy": "telcocli"},
        ]

        account = {"Name": "Some Account", "Id": "123456789012"}

        for tags in test_cases:
            result = AccountTypeDetector.determine_account_type(account, tags)
            assert result == ACCOUNT_TYPE_PARTNER, f"Account with tags {tags} should be partner"

    def test_determine_partner_account_by_partner_tag(self):
        """Test detection of partner account by Partner tag."""
        account = {"Name": "Some Account", "Id": "123456789012"}
        tags = {"Partner": "SomePartner"}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_PARTNER

    def test_determine_partner_account_by_name_keyword(self):
        """Test detection of partner account by name keyword."""
        account = {"Name": "aws-5gc-pmt-test-account", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_PARTNER

    def test_determine_legacy_account_by_prefix(self):
        """Test detection of legacy account by name prefix."""
        account = {"Name": "csectl-legacy-account", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_LEGACY

    def test_determine_legacy_account_by_keyword(self):
        """Test detection of legacy account by keyword in name."""
        account = {"Name": "old-csectl-system", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_LEGACY

    def test_determine_default_legacy_account(self):
        """Test that unclassified accounts default to legacy."""
        account = {"Name": "Unknown Account Type", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_LEGACY

    def test_case_insensitive_name_matching(self):
        """Test that name matching is case insensitive."""
        test_cases = [
            ({"Name": "MANAGEMENT ACCOUNT", "Id": "123456789012"}, ACCOUNT_TYPE_MANAGEMENT),
            ({"Name": "log archive", "Id": "123456789012"}, ACCOUNT_TYPE_SECURITY),
            ({"Name": "AWS-5GC-PMT-TEST", "Id": "123456789012"}, ACCOUNT_TYPE_PARTNER),
            ({"Name": "CSECTL-LEGACY", "Id": "123456789012"}, ACCOUNT_TYPE_LEGACY),
        ]

        for account, expected_type in test_cases:
            tags = {}
            result = AccountTypeDetector.determine_account_type(account, tags)
            assert result == expected_type, f"Account {account['Name']} should be {expected_type}"

    def test_priority_order_management_over_others(self):
        """Test that management account detection has priority."""
        # Account that could match multiple types but has management tag
        account = {"Name": "security-management-account", "Id": "123456789012"}
        tags = {"AccountType": "management"}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_MANAGEMENT

    def test_priority_order_security_over_partner(self):
        """Test that security account detection has priority over partner."""
        # Account that could match both security and partner
        account = {"Name": "audit-aws-5gc-pmt", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_SECURITY

    def test_priority_order_partner_over_legacy(self):
        """Test that partner account detection has priority over legacy."""
        # Account that could match both partner and legacy
        account = {"Name": "aws-5gc-pmt-csectl", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_PARTNER

    def test_empty_account_name(self):
        """Test handling of empty account name."""
        account = {"Name": "", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_LEGACY

    def test_empty_tags(self):
        """Test handling of empty tags."""
        account = {"Name": "Test Account", "Id": "123456789012"}
        tags = {}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_LEGACY

    def test_none_values_in_tags(self):
        """Test handling of None values in tags."""
        account = {"Name": "Test Account", "Id": "123456789012"}
        tags = {"ManagedBy": None, "Partner": None}

        result = AccountTypeDetector.determine_account_type(account, tags)
        assert result == ACCOUNT_TYPE_LEGACY


class TestAccountTypeDetectorPrivateMethods:
    """Test cases for private methods of AccountTypeDetector."""

    def test_is_management_account_by_name(self):
        """Test _is_management_account method with name matching."""
        assert AccountTypeDetector._is_management_account("management account", {}) is True
        assert AccountTypeDetector._is_management_account("test account", {}) is False

    def test_is_management_account_by_tag(self):
        """Test _is_management_account method with tag matching."""
        assert (
            AccountTypeDetector._is_management_account("test", {"AccountType": "management"})
            is True
        )
        assert AccountTypeDetector._is_management_account("test", {"AccountType": "other"}) is False

    def test_is_security_account_exact_match(self):
        """Test _is_security_account method with exact name matching."""
        assert AccountTypeDetector._is_security_account("log archive", {}) is True
        assert AccountTypeDetector._is_security_account("audit", {}) is True
        assert AccountTypeDetector._is_security_account("test", {}) is False

    def test_is_security_account_keyword_match(self):
        """Test _is_security_account method with keyword matching."""
        assert AccountTypeDetector._is_security_account("security operations", {}) is True
        assert AccountTypeDetector._is_security_account("test security", {}) is True
        assert AccountTypeDetector._is_security_account("test", {}) is False

    def test_is_partner_account_by_managed_by(self):
        """Test _is_partner_account method with ManagedBy tag."""
        assert AccountTypeDetector._is_partner_account("test", {"ManagedBy": "awstelco"}) is True
        assert AccountTypeDetector._is_partner_account("test", {"ManagedBy": "telcocli"}) is True
        assert AccountTypeDetector._is_partner_account("test", {"ManagedBy": "other"}) is False

    def test_is_partner_account_by_partner_tag(self):
        """Test _is_partner_account method with Partner tag."""
        assert AccountTypeDetector._is_partner_account("test", {"Partner": "value"}) is True
        assert AccountTypeDetector._is_partner_account("test", {}) is False

    def test_is_partner_account_by_name(self):
        """Test _is_partner_account method with name matching."""
        assert AccountTypeDetector._is_partner_account("aws-5gc-pmt-test", {}) is True
        assert AccountTypeDetector._is_partner_account("test", {}) is False

    def test_is_legacy_account_by_prefix(self):
        """Test _is_legacy_account method with prefix matching."""
        assert AccountTypeDetector._is_legacy_account("csectl-test", {}) is True
        assert AccountTypeDetector._is_legacy_account("test", {}) is False

    def test_is_legacy_account_by_keyword(self):
        """Test _is_legacy_account method with keyword matching."""
        assert AccountTypeDetector._is_legacy_account("test-csectl-system", {}) is True
        assert AccountTypeDetector._is_legacy_account("test", {}) is False
