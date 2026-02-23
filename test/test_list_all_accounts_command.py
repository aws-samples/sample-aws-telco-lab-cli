"""Tests for List All Accounts Command.

Note: All AWS account IDs in this test file are example/mock values.
These are test fixtures and do not represent real AWS resources.
"""

import argparse
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.commands.list_all_accounts import ListAllAccountsCommand
from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.utils.account_constants import (
    ACCOUNT_TYPE_LEGACY,
    ACCOUNT_TYPE_MANAGEMENT,
    ACCOUNT_TYPE_PARTNER,
    ACCOUNT_TYPE_SECURITY,
    ROOT_OU_NAME,
    UNKNOWN_OU,
)


class TestListAllAccountsCommand:
    """Test cases for ListAllAccountsCommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = ListAllAccountsCommand()

    @pytest.fixture
    def mock_accounts(self):
        return [
            {
                "Id": "123456789012",
                "Name": "aws-5gc-pmt-TEST_iam_trust",
                "Email": "test@example.com",
                "Status": "ACTIVE",
                "JoinedMethod": "INVITED",
                "JoinedTimestamp": datetime(2023, 1, 1),
            },
            {
                "Id": "123456789013",
                "Name": "Management Account",
                "Email": "mgmt@example.com",
                "Status": "ACTIVE",
                "JoinedMethod": "CREATED",
                "JoinedTimestamp": datetime(2023, 1, 2),
            },
            {
                "Id": "123456789014",
                "Name": "Audit",
                "Email": "audit@example.com",
                "Status": "SUSPENDED",
                "JoinedMethod": "INVITED",
                "JoinedTimestamp": datetime(2023, 1, 3),
            },
        ]

    def test_name_property(self):
        """Test command name."""
        assert self.command.name == "list-all-accounts"

    def test_description_property(self):
        """Test command description."""
        assert "List all accounts in AWS Organizations" in self.command.description

    def test_register_arguments(self):
        """Test argument registration."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        args = parser.parse_args(
            ["--status", "ACTIVE", "--account-type", "partner", "--output", "table", "--include-ou"]
        )
        assert args.status == "ACTIVE"
        assert args.account_type == "partner"
        assert args.output == "table"
        assert args.include_ou is True

    def test_run_basic_validation(self):
        """Test basic command validation."""
        args = Mock()
        args.status = None
        args.account_type = None
        args.output = "json"

        # Test that command has required methods
        assert hasattr(self.command, "run")
        assert hasattr(self.command, "_list_all_accounts_detailed")

        # Verify args are properly set
        assert args.output == "json"

    def test_determine_account_type(self):
        """Test account type determination using AccountTypeDetector."""
        from telco_cli.utils.account_type_detector import AccountTypeDetector

        # Test partner account
        partner_account = {"Name": "aws-5gc-pmt-TEST_iam_trust", "Id": "123456789012"}
        assert (
            AccountTypeDetector.determine_account_type(partner_account, {}) == ACCOUNT_TYPE_PARTNER
        )

        # Test management account
        mgmt_account = {"Name": "Management Account", "Id": "123456789012"}
        assert (
            AccountTypeDetector.determine_account_type(mgmt_account, {}) == ACCOUNT_TYPE_MANAGEMENT
        )

        # Test security account
        security_account = {"Name": "Audit", "Id": "123456789012"}
        assert (
            AccountTypeDetector.determine_account_type(security_account, {})
            == ACCOUNT_TYPE_SECURITY
        )

        # Test legacy account
        legacy_account = {"Name": "CSECTL-legacy", "Id": "123456789012"}
        assert AccountTypeDetector.determine_account_type(legacy_account, {}) == ACCOUNT_TYPE_LEGACY

    def test_run_with_filters(self):
        """Test command execution with filters."""
        args = Mock()
        args.status = "ACTIVE"
        args.account_type = "partner"
        args.output = "json"

        # Test filter validation
        assert args.status == "ACTIVE"
        assert args.account_type == "partner"

    def test_run_success(self):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.output = "json"
        args.include_ou = False

        mock_result = {"Success": True, "Accounts": [], "TotalCount": 0, "Summary": {}}

        with (
            patch.object(self.command, "_list_all_accounts_detailed", return_value=mock_result),
            patch("telco_cli.commands.list_all_accounts.get_formatter") as mock_formatter,
        ):

            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance
            self.command.run(args)
            mock_formatter_instance.format_success.assert_called_once_with(mock_result, "json")

    def test_run_with_exception(self):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.output = "json"

        with (
            patch.object(
                self.command, "_list_all_accounts_detailed", side_effect=Exception("Test error")
            ),
            patch("telco_cli.commands.list_all_accounts.get_formatter") as mock_formatter,
            patch("sys.exit") as mock_exit,
        ):

            mock_formatter_instance = Mock()
            mock_formatter_instance.get_exit_code.return_value = 1
            mock_formatter.return_value = mock_formatter_instance
            self.command.run(args)
            mock_formatter_instance.format_error.assert_called_once()
            mock_exit.assert_called_once_with(1)

    @patch("boto3.client")
    def test_list_all_accounts_detailed_success(self, mock_boto_client, mock_accounts):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.include_ou = False

        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client

        mock_paginator = Mock()
        mock_org_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Accounts": mock_accounts}]

        mock_org_client.list_tags_for_resource.return_value = {"Tags": []}

        with patch(
            "telco_cli.commands.list_all_accounts.AccountTypeDetector.determine_account_type"
        ) as mock_detector:
            mock_detector.side_effect = [
                ACCOUNT_TYPE_PARTNER,
                ACCOUNT_TYPE_MANAGEMENT,
                ACCOUNT_TYPE_SECURITY,
            ]

            result = self.command._list_all_accounts_detailed(args)
            assert result["Success"] is True
            assert result["TotalCount"] == 3
            assert len(result["Accounts"]) == 3
            assert "Summary" in result
            assert "FilteredBy" in result

    @patch("boto3.client")
    def test_list_all_accounts_with_status_filter(self, mock_boto_client, mock_accounts):
        args = Mock()
        args.status = "ACTIVE"
        args.account_type = "all"
        args.include_ou = False
        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_paginator = Mock()
        mock_org_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Accounts": mock_accounts}]
        mock_org_client.list_tags_for_resource.return_value = {"Tags": []}

        with patch(
            "telco_cli.commands.list_all_accounts.AccountTypeDetector.determine_account_type"
        ) as mock_detector:
            mock_detector.side_effect = [
                ACCOUNT_TYPE_PARTNER,
                ACCOUNT_TYPE_MANAGEMENT,
                ACCOUNT_TYPE_SECURITY,
            ]
            result = self.command._list_all_accounts_detailed(args)
            assert result["TotalCount"] == 2
            for account in result["Accounts"]:
                assert account["Status"] == "ACTIVE"

    @patch("boto3.client")
    def test_list_all_accounts_with_type_filter(self, mock_boto_client, mock_accounts):
        args = Mock()
        args.status = None
        args.account_type = "partner"
        args.include_ou = False

        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_paginator = Mock()
        mock_org_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Accounts": mock_accounts}]
        mock_org_client.list_tags_for_resource.return_value = {"Tags": []}

        with patch(
            "telco_cli.commands.list_all_accounts.AccountTypeDetector.determine_account_type"
        ) as mock_detector:
            mock_detector.side_effect = [
                ACCOUNT_TYPE_PARTNER,
                ACCOUNT_TYPE_MANAGEMENT,
                ACCOUNT_TYPE_SECURITY,
            ]

            result = self.command._list_all_accounts_detailed(args)
            assert result["TotalCount"] == 1
            assert result["Accounts"][0]["AccountType"] == "partner"

    @patch("boto3.client")
    def test_list_all_accounts_with_ou_info(self, mock_boto_client, mock_accounts):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.include_ou = True
        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_paginator = Mock()
        mock_org_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Accounts": mock_accounts[:1]}]
        mock_org_client.list_tags_for_resource.return_value = {"Tags": []}

        with (
            patch.object(self.command, "_get_ou_information") as mock_get_ou,
            patch(
                "telco_cli.commands.list_all_accounts.AccountTypeDetector.determine_account_type"
            ) as mock_detector,
        ):

            mock_get_ou.return_value = {"Id": "ou-123", "Name": "TestOU"}
            mock_detector.return_value = ACCOUNT_TYPE_PARTNER
            result = self.command._list_all_accounts_detailed(args)
            assert result["TotalCount"] == 1
            assert "OrganizationalUnit" in result["Accounts"][0]
            assert result["Accounts"][0]["OrganizationalUnit"]["Name"] == "TestOU"

    def test_get_ou_information_with_ou(self):
        mock_org_client = Mock()
        mock_org_client.list_parents.return_value = {"Parents": [{"Id": "ou-123456789"}]}
        mock_org_client.describe_organizational_unit.return_value = {
            "OrganizationalUnit": {"Name": "TestOU"}
        }
        result = self.command._get_ou_information(mock_org_client, "123456789012")
        assert result["Id"] == "ou-123456789"
        assert result["Name"] == "TestOU"

    def test_get_ou_information_with_root(self):
        mock_org_client = Mock()
        mock_org_client.list_parents.return_value = {"Parents": [{"Id": "r-123456789"}]}
        result = self.command._get_ou_information(mock_org_client, "123456789012")
        assert result["Id"] == "r-123456789"
        assert result["Name"] == ROOT_OU_NAME

    def test_get_ou_information_with_error(self):
        mock_org_client = Mock()
        mock_org_client.list_parents.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "ListParents"
        )
        result = self.command._get_ou_information(mock_org_client, "123456789012")
        assert result == UNKNOWN_OU

    def test_generate_summary(self):
        accounts = [
            {
                "Status": "ACTIVE",
                "AccountType": "partner",
                "OrganizationalUnit": {"Name": "PartnerOU"},
            },
            {
                "Status": "ACTIVE",
                "AccountType": "management",
                "OrganizationalUnit": {"Name": "CoreOU"},
            },
            {"Status": "SUSPENDED", "AccountType": "partner"},
        ]
        result = self.command._generate_summary(accounts)
        assert result["TotalAccounts"] == 3
        assert result["ByStatus"]["ACTIVE"] == 2
        assert result["ByStatus"]["SUSPENDED"] == 1
        assert result["ByType"]["partner"] == 2
        assert result["ByType"]["management"] == 1
        assert result["ActiveByType"]["partner"] == 1
        assert result["ActiveByType"]["management"] == 1
        assert "PartnerOU" in result["OrganizationalUnits"]
        assert "CoreOU" in result["OrganizationalUnits"]

    @patch("boto3.client")
    def test_list_all_accounts_organizations_not_enabled(self, mock_boto_client):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.include_ou = False
        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_org_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "AWSOrganizationsNotInUseException"}}, "ListAccounts"
        )
        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._list_all_accounts_detailed(args)
        assert exc_info.value.error_code == ErrorCode.ORGANIZATIONS_NOT_ENABLED

    @patch("boto3.client")
    def test_list_all_accounts_access_denied(self, mock_boto_client):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.include_ou = False
        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_org_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "ListAccounts"
        )
        with pytest.raises(TelcoCLIException) as exc_info:
            self.command._list_all_accounts_detailed(args)
        assert exc_info.value.error_code == ErrorCode.ORGANIZATIONS_ACCESS_DENIED

    @patch("boto3.client")
    def test_list_all_accounts_other_client_error(self, mock_boto_client):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.include_ou = False
        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_org_client.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "UnknownError"}}, "ListAccounts"
        )
        with pytest.raises(ClientError):
            self.command._list_all_accounts_detailed(args)

    @patch("boto3.client")
    def test_list_all_accounts_with_tags(self, mock_boto_client, mock_accounts):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.include_ou = False
        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_paginator = Mock()
        mock_org_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Accounts": mock_accounts[:1]}]
        mock_org_client.list_tags_for_resource.return_value = {
            "Tags": [{"Key": "Environment", "Value": "Production"}]
        }

        with patch(
            "telco_cli.commands.list_all_accounts.AccountTypeDetector.determine_account_type"
        ) as mock_detector:
            mock_detector.return_value = ACCOUNT_TYPE_PARTNER
            result = self.command._list_all_accounts_detailed(args)
            assert result["TotalCount"] == 1
            assert result["Accounts"][0]["Tags"]["Environment"] == "Production"

    @patch("boto3.client")
    def test_list_all_accounts_tags_error(self, mock_boto_client, mock_accounts):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.include_ou = False
        mock_org_client = Mock()
        mock_boto_client.return_value = mock_org_client
        mock_paginator = Mock()
        mock_org_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Accounts": mock_accounts[:1]}]
        mock_org_client.list_tags_for_resource.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "ListTagsForResource"
        )

        with patch(
            "telco_cli.commands.list_all_accounts.AccountTypeDetector.determine_account_type"
        ) as mock_detector:
            mock_detector.return_value = ACCOUNT_TYPE_PARTNER
            result = self.command._list_all_accounts_detailed(args)
            assert result["TotalCount"] == 1
            assert result["Accounts"][0]["Tags"] == {}

    def test_telcocli_exception_reraised_in_run(self):
        args = Mock()
        args.status = None
        args.account_type = "all"
        args.output = "json"

        original_exception = TelcoCLIException(
            ErrorCode.ORGANIZATIONS_NOT_ENABLED, "Organizations not enabled"
        )

        with (
            patch.object(
                self.command, "_list_all_accounts_detailed", side_effect=original_exception
            ),
            patch("telco_cli.commands.list_all_accounts.get_formatter") as mock_formatter,
        ):

            mock_formatter_instance = Mock()
            mock_formatter.return_value = mock_formatter_instance

            with pytest.raises(TelcoCLIException) as exc_info:
                self.command.run(args)

            assert exc_info.value is original_exception
            assert exc_info.value.error_code == ErrorCode.ORGANIZATIONS_NOT_ENABLED
