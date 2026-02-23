# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Update credentials command."""

import argparse
import configparser
import json
import re
import sys
from pathlib import Path

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, console_error, get_logger

logger = get_logger(__name__)


class UpdateCredentialsCommand(BaseCommand):
    """Update AWS credentials from credential sources."""

    @property
    def name(self) -> str:
        return "update-credentials"

    @property
    def description(self) -> str:
        return "Update AWS credentials (supports various credential formats)"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("account_id", help="AWS account ID")
        parser.add_argument(
            "--format",
            choices=["interactive", "stdin"],
            default="interactive",
            help="Input format (default: interactive)",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the update credentials command."""
        try:
            logger.info(f"Updating credentials for account: {args.account_id}")

            mappings = self._load_account_mappings()
            profiles = mappings.get(args.account_id, [])

            if not profiles:
                console_error.print(f"No profiles configured for account {args.account_id}")
                console.print(
                    f"Configure with: telcocli configure-credentials add {args.account_id} profile1,profile2"
                )
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    f"No profiles configured for account {args.account_id}",
                )

            console.print(f"Account: {args.account_id}")
            console.print(f"Will update profiles: {', '.join(profiles)}")
            console.print()

            if args.format == "interactive":
                credentials = self._get_interactive_credentials()
            else:
                credentials = self._get_stdin_credentials()

            if not credentials:
                raise TelcoCLIException(
                    ErrorCode.CREDENTIAL_PARSE_ERROR, "Could not parse credentials"
                )

            console.print("Parsed credentials:")
            console.print(f"  Access Key: {credentials['access_key'][:8]}***")
            console.print(f"  Secret Key: ***{credentials['secret_key'][-4:]}")
            console.print(f"  Session Token: ***{credentials['session_token'][-8:]}")
            console.print()

            # Update profiles
            success_count = 0
            for profile in profiles:
                try:
                    self._update_aws_credentials(
                        credentials["access_key"],
                        credentials["secret_key"],
                        credentials["session_token"],
                        profile,
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error updating profile '{profile}': {e}")
                    console_error.print(f"Error updating profile '{profile}': {e}")

            console.print(f"Updated {success_count}/{len(profiles)} profiles successfully")

        except TelcoCLIException:
            raise
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            raise TelcoCLIException(ErrorCode.USER_CANCELLED, "Operation cancelled by user")
        except Exception as e:
            logger.exception("Unexpected error during credential update")
            raise TelcoCLIException(ErrorCode.CREDENTIAL_PARSE_ERROR, str(e))

    def _load_account_mappings(self) -> dict:
        """Load account to profile mappings."""
        config_file = Path.home() / ".aws" / "account_mappings.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load account mappings: {e}")
                return {}
        return {}

    def _get_interactive_credentials(self) -> dict:
        """Get credentials through interactive input."""
        console.print("Paste AWS credentials in one of these formats:")
        console.print("  • AWS CLI export format: export AWS_ACCESS_KEY_ID=...")
        console.print("  • Windows SET format: set AWS_ACCESS_KEY_ID=...")
        console.print("(Press Enter on empty line when done)")
        console.print()

        lines = []
        while True:
            try:
                line = input().strip()
                if not line:
                    break
                lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break

        cred_text = "\n".join(lines)
        return self._parse_credentials(cred_text)

    def _get_stdin_credentials(self) -> dict:
        """Get credentials from stdin."""
        cred_text = sys.stdin.read().strip()
        return self._parse_credentials(cred_text)

    def _parse_credentials(self, text: str) -> dict:
        """Parse both Windows SET and bash export credential formats."""
        # Try Windows SET format first
        set_patterns = {
            "access_key": r"set\s+AWS_ACCESS_KEY_ID=([A-Z0-9]+)",
            "secret_key": r"set\s+AWS_SECRET_ACCESS_KEY=([A-Za-z0-9/+=]+)",
            "session_token": r"set\s+AWS_SESSION_TOKEN=([A-Za-z0-9/+=]+)",
        }

        credentials = {}
        for key, pattern in set_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                credentials[key] = match.group(1)

        # If SET format found all 3, return it
        if len(credentials) == 3:
            return credentials

        # Try bash export format if SET format didn't find all credentials
        if len(credentials) < 3:
            export_patterns = {
                "access_key": r"export\s+AWS_ACCESS_KEY_ID=([A-Z0-9]+)",
                "secret_key": r"export\s+AWS_SECRET_ACCESS_KEY=([A-Za-z0-9/+=]+)",
                "session_token": r"export\s+AWS_SESSION_TOKEN=([A-Za-z0-9/+=]+)",
            }

            for key, pattern in export_patterns.items():
                if key not in credentials:  # Only add if not already found
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        credentials[key] = match.group(1)

        return credentials if len(credentials) == 3 else {}

    def _update_aws_credentials(
        self, access_key: str, secret_key: str, session_token: str, profile_name: str
    ) -> None:
        """Update AWS credentials for specified profile."""
        try:
            credentials_file = Path.home() / ".aws" / "credentials"
            credentials_file.parent.mkdir(exist_ok=True)

            config = configparser.ConfigParser()
            if credentials_file.exists():
                config.read(credentials_file)

            if profile_name not in config:
                config.add_section(profile_name)

            config[profile_name]["aws_access_key_id"] = access_key
            config[profile_name]["aws_secret_access_key"] = secret_key
            config[profile_name]["aws_session_token"] = session_token

            with open(credentials_file, "w") as f:
                config.write(f)

            console.print(
                f"[green][OK] Updated AWS credentials for profile '{profile_name}'[/green]"
            )
        except (IOError, PermissionError, configparser.Error) as e:
            logger.error(f"Failed to update credentials for profile '{profile_name}': {e}")
            raise TelcoCLIException(
                ErrorCode.CREDENTIAL_PARSE_ERROR, f"Failed to update credentials: {e}"
            )
