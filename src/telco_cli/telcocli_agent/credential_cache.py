# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Credential validation caching to avoid repeated STS calls."""

import logging
import time
from typing import Dict, List, Optional, Tuple

import boto3

logger = logging.getLogger(__name__)

# Global cache for credential validation results
_credential_cache: Dict[str, Tuple[bool, str, float]] = {}
_CACHE_TTL = 300  # 5 minutes


def _get_cache_key(profile: Optional[str] = None) -> str:
    """Generate cache key for credential validation."""
    import os

    if profile:
        return f"profile:{profile}"

    # Only log first 8 chars of access key for security
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    profile_env = os.environ.get("AWS_PROFILE", "default")
    return f"env:{profile_env}:{access_key[:8] if access_key else 'none'}"


def _is_cache_valid(timestamp: float) -> bool:
    """Check if cache entry is still valid."""
    return time.time() - timestamp < _CACHE_TTL


def validate_credentials_cached(profile: Optional[str] = None) -> Tuple[bool, str]:
    """Validate AWS credentials with caching.

    Args:
        profile: AWS profile name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    cache_key = _get_cache_key(profile)
    current_time = time.time()

    # Check cache first
    if cache_key in _credential_cache:
        is_valid, error_msg, timestamp = _credential_cache[cache_key]
        if _is_cache_valid(timestamp):
            logger.debug(f"Using cached credential validation for {cache_key}")
            return is_valid, error_msg

    # Cache miss or expired - validate credentials
    logger.debug(f"Validating credentials for {cache_key}")

    try:
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        sts = session.client("sts")

        # Quick STS call to validate credentials
        response = sts.get_caller_identity()

        is_valid = True
        error_msg = ""
        logger.debug(f"Credentials valid for account: {response.get('Account', 'unknown')}")

    except Exception as e:
        is_valid = False
        error_msg = str(e)
        logger.debug(f"Credential validation failed: {error_msg}")

    # Cache the result
    _credential_cache[cache_key] = (is_valid, error_msg, current_time)

    return is_valid, error_msg


def get_valid_profiles_cached() -> List[str]:
    """Get list of valid AWS profiles with caching."""
    import configparser
    from pathlib import Path

    credentials_file = Path.home() / ".aws" / "credentials"
    if not credentials_file.exists():
        return []

    config = configparser.ConfigParser()
    try:
        config.read(credentials_file)
    except Exception:
        return []

    valid_profiles = []

    for profile_name in config.sections():
        is_valid, _ = validate_credentials_cached(profile_name)
        if is_valid:
            valid_profiles.append(profile_name)

    return valid_profiles


def clear_credential_cache():
    """Clear the credential cache (useful for testing or forced refresh)."""
    _credential_cache.clear()
    logger.debug("Credential cache cleared")


def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics for monitoring."""
    valid_entries = sum(
        1 for _, _, timestamp in _credential_cache.values() if _is_cache_valid(timestamp)
    )

    return {
        "total_entries": len(_credential_cache),
        "valid_entries": valid_entries,
        "expired_entries": len(_credential_cache) - valid_entries,
    }
