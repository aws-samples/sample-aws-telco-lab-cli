# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Centralized credential management for TelcoCLI agent."""

import configparser
import logging
from pathlib import Path
from typing import List, Tuple


class CredentialManager:
    """Manages AWS credential validation and profile operations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_valid_profiles(self) -> List[str]:
        """Get list of valid AWS profiles."""
        valid_profiles = []

        # Suppress boto3 warnings during validation
        boto_logger = logging.getLogger("botocore")
        original_level = boto_logger.level
        boto_logger.setLevel(logging.ERROR)

        try:
            credentials_file = Path.home() / ".aws" / "credentials"
            if credentials_file.exists():
                config = configparser.ConfigParser()
                config.read(credentials_file)

                for profile_name in config.sections():
                    if self._validate_profile(profile_name):
                        valid_profiles.append(profile_name)
        except (OSError, configparser.Error, ValueError) as e:
            self.logger.debug(f"Error reading credentials file: {e}")
        finally:
            boto_logger.setLevel(original_level)

        return valid_profiles

    def _validate_profile(self, profile_name: str) -> bool:
        """Validate a single AWS profile with caching."""
        from .credential_cache import validate_credentials_cached

        is_valid, _ = validate_credentials_cached(profile_name)
        return is_valid

    def check_credentials(self) -> Tuple[bool, List[str], List[str]]:
        """Check AWS credentials status.

        Returns:
            Tuple of (has_valid_credentials, valid_profiles, invalid_profiles)
        """
        credentials_file = Path.home() / ".aws" / "credentials"
        if not credentials_file.exists():
            return False, [], []

        valid_profiles = []
        invalid_profiles = []

        # Suppress boto3 warnings during check
        boto_logger = logging.getLogger("botocore")
        original_level = boto_logger.level
        boto_logger.setLevel(logging.ERROR)

        try:
            config = configparser.ConfigParser()
            config.read(credentials_file)

            for profile_name in config.sections():
                if self._validate_profile(profile_name):
                    valid_profiles.append(profile_name)
                else:
                    invalid_profiles.append(profile_name)
        except (OSError, configparser.Error, ValueError) as e:
            self.logger.debug(f"Error checking credentials: {e}")
        finally:
            boto_logger.setLevel(original_level)

        return len(valid_profiles) > 0, valid_profiles, invalid_profiles
