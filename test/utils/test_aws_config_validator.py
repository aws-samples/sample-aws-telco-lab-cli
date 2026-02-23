"""Tests for AWS config validator."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from telco_cli.utils.aws_config_validator import AWSConfigValidator


class TestAWSConfigValidator:
    """Test cases for AWSConfigValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = AWSConfigValidator()

    def test_init(self):
        """Test validator initialization."""
        assert isinstance(self.validator.aws_config_path, Path)
        assert isinstance(self.validator.aws_credentials_path, Path)
        assert self.validator.REQUIRED_PROFILES == ["default"]

    @patch("subprocess.run")
    def test_is_aws_cli_installed_success(self, mock_run):
        """Test AWS CLI detection when installed."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.validator._is_aws_cli_installed()

        assert result is True
        mock_run.assert_called_once_with(
            ["aws", "--version"],
            capture_output=True,
            check=True,
            timeout=5,
        )

    @patch("subprocess.run")
    def test_is_aws_cli_installed_not_found(self, mock_run):
        """Test AWS CLI detection when not installed."""
        mock_run.side_effect = FileNotFoundError()

        result = self.validator._is_aws_cli_installed()

        assert result is False

    @patch("subprocess.run")
    def test_is_aws_cli_installed_timeout(self, mock_run):
        """Test AWS CLI detection timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("aws", 5)

        result = self.validator._is_aws_cli_installed()

        assert result is False

    @patch("builtins.open", new_callable=mock_open, read_data="[default]\n[profile test]\n")
    @patch.object(Path, "exists")
    def test_get_configured_profiles_config_file(self, mock_exists, mock_file):
        """Test getting profiles from config file."""
        mock_exists.return_value = True

        profiles = self.validator._get_configured_profiles()

        assert "default" in profiles
        assert "test" in profiles

    @patch("builtins.open", new_callable=mock_open, read_data="[default]\n[test-profile]\n")
    @patch.object(Path, "exists")
    def test_get_configured_profiles_credentials_file(self, mock_exists, mock_file):
        """Test getting profiles from credentials file."""
        mock_exists.return_value = True

        profiles = self.validator._get_configured_profiles()

        assert "default" in profiles
        assert "test-profile" in profiles

    @patch("subprocess.run")
    def test_test_credentials_success(self, mock_run):
        """Test credential validation success."""
        mock_run.return_value = MagicMock(returncode=0)

        result = self.validator._test_credentials()

        assert result is True
        mock_run.assert_called_once_with(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            check=True,
            timeout=10,
        )

    @patch("subprocess.run")
    def test_test_credentials_failure(self, mock_run):
        """Test credential validation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "aws")

        result = self.validator._test_credentials()

        assert result is False

    @patch.object(Path, "exists")
    @patch.object(AWSConfigValidator, "_test_credentials")
    @patch.object(AWSConfigValidator, "_get_configured_profiles")
    @patch.object(AWSConfigValidator, "_is_aws_cli_installed")
    def test_validate_success(self, mock_cli, mock_profiles, mock_creds, mock_exists):
        """Test successful validation."""
        mock_cli.return_value = True
        mock_profiles.return_value = ["default", "test"]
        mock_creds.return_value = True
        mock_exists.return_value = True

        is_valid, error = self.validator.validate()

        assert is_valid is True
        assert error is None

    @patch.object(AWSConfigValidator, "_is_aws_cli_installed")
    def test_validate_no_cli(self, mock_cli):
        """Test validation when AWS CLI not installed."""
        mock_cli.return_value = False

        is_valid, error = self.validator.validate()

        assert is_valid is False
        assert "AWS CLI is not installed" in error

    @patch.object(AWSConfigValidator, "_test_credentials")
    @patch.object(AWSConfigValidator, "_get_configured_profiles")
    @patch.object(AWSConfigValidator, "_is_aws_cli_installed")
    @patch.object(Path, "exists")
    def test_validate_no_config(self, mock_exists, mock_cli, mock_profiles, mock_creds):
        """Test validation when no config files exist."""
        mock_exists.return_value = False
        mock_cli.return_value = True

        is_valid, error = self.validator.validate()

        assert is_valid is False
        assert "AWS configuration not found" in error

    @patch.object(Path, "exists")
    @patch.object(AWSConfigValidator, "_test_credentials")
    @patch.object(AWSConfigValidator, "_get_configured_profiles")
    @patch.object(AWSConfigValidator, "_is_aws_cli_installed")
    def test_validate_missing_profiles(self, mock_cli, mock_profiles, mock_creds, mock_exists):
        """Test validation when required profiles missing."""
        mock_cli.return_value = True
        mock_profiles.return_value = ["test"]  # Missing default
        mock_exists.return_value = True

        is_valid, error = self.validator.validate()

        assert is_valid is False
        assert "Missing required AWS profiles: default" in error

    @patch.object(Path, "exists")
    @patch.object(AWSConfigValidator, "_test_credentials")
    @patch.object(AWSConfigValidator, "_get_configured_profiles")
    @patch.object(AWSConfigValidator, "_is_aws_cli_installed")
    def test_validate_invalid_credentials(self, mock_cli, mock_profiles, mock_creds, mock_exists):
        """Test validation when credentials are invalid."""
        mock_cli.return_value = True
        mock_profiles.return_value = ["default"]
        mock_creds.return_value = False
        mock_exists.return_value = True

        is_valid, error = self.validator.validate()

        assert is_valid is False
        assert "AWS credentials are invalid or expired" in error

    def test_get_setup_instructions(self):
        """Test setup instructions."""
        instructions = self.validator.get_setup_instructions()

        assert "AWS Configuration Required" in instructions
        assert "aws configure" in instructions
        assert "aws sts get-caller-identity" in instructions
