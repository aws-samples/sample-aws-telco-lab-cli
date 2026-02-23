# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""AWS configuration validation for TelcoCLI."""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class AWSConfigValidator:
    """Validates AWS CLI configuration and profiles."""

    REQUIRED_PROFILES = ["default"]  # Minimum required profiles

    def __init__(self):
        """Initialize validator."""
        self.aws_config_path = Path.home() / ".aws" / "config"
        self.aws_credentials_path = Path.home() / ".aws" / "credentials"

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate AWS configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if AWS CLI is installed
        if not self._is_aws_cli_installed():
            return False, "AWS CLI is not installed"

        # Check if config files exist
        if not self.aws_config_path.exists() and not self.aws_credentials_path.exists():
            return False, "AWS configuration not found (~/.aws/config or ~/.aws/credentials)"

        # Check for required profiles
        profiles = self._get_configured_profiles()
        missing = [p for p in self.REQUIRED_PROFILES if p not in profiles]

        if missing:
            return False, f"Missing required AWS profiles: {', '.join(missing)}"

        # Validate credentials work
        if not self._test_credentials():
            return False, "AWS credentials are invalid or expired"

        return True, None

    def get_setup_instructions(self) -> str:
        """Get instructions for setting up AWS configuration."""
        return """
🔧 AWS Configuration Required

TelcoCLI requires AWS CLI to be configured with valid credentials.

Setup Steps:
1. Install AWS CLI (if not installed):
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install

2. Configure AWS credentials:
   aws configure

   You'll be prompted for:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., us-west-2)
   - Default output format (json recommended)

3. For multiple profiles (recommended for Telco operations):
   aws configure --profile telco-admin
   aws configure --profile telco-partner

4. Verify configuration:
   aws sts get-caller-identity

For more information: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html
"""

    def _is_aws_cli_installed(self) -> bool:
        """Check if AWS CLI is installed."""
        try:
            subprocess.run(
                ["aws", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_configured_profiles(self) -> List[str]:
        """Get list of configured AWS profiles."""
        profiles = set()

        # Check credentials file
        if self.aws_credentials_path.exists():
            with open(self.aws_credentials_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("[") and line.endswith("]"):
                        profile = line[1:-1]
                        profiles.add(profile)

        # Check config file
        if self.aws_config_path.exists():
            with open(self.aws_config_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("[profile ") and line.endswith("]"):
                        profile = line[9:-1]
                        profiles.add(profile)
                    elif line.startswith("[") and line.endswith("]") and line != "[default]":
                        profile = line[1:-1]
                        if profile.startswith("profile "):
                            profile = profile[8:]
                        profiles.add(profile)

        # Default profile is implicit if credentials exist
        if self.aws_credentials_path.exists():
            profiles.add("default")

        return list(profiles)

    def _test_credentials(self) -> bool:
        """Test if AWS credentials are valid."""
        try:
            result = subprocess.run(
                ["aws", "sts", "get-caller-identity"],
                capture_output=True,
                check=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
