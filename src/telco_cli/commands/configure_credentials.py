# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Configure credential mappings command."""

import argparse
import json
from pathlib import Path

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, console_error, get_logger

logger = get_logger(__name__)


class ConfigureCredentialsCommand(BaseCommand):
    """Configure AWS account to profile mappings."""

    @property
    def name(self) -> str:
        return "configure-credentials"

    @property
    def description(self) -> str:
        return "Configure AWS account to profile mappings"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        subparsers = parser.add_subparsers(dest="action", required=True, help="Action to perform")

        # Add mapping
        add_parser = subparsers.add_parser("add", help="Add account to profile mapping")
        add_parser.add_argument("account_id", help="AWS account ID")
        add_parser.add_argument("profiles", help="Comma-separated list of AWS profiles")

        # List mappings
        subparsers.add_parser("list", help="List all configured mappings")

        # Remove mapping
        remove_parser = subparsers.add_parser("remove", help="Remove account mapping")
        remove_parser.add_argument("account_id", help="AWS account ID to remove")

    def run(self, args: argparse.Namespace) -> None:
        """Execute the configure credentials command."""
        try:
            logger.info(f"Executing configure-credentials with action: {args.action}")

            if args.action == "add":
                self._add_mapping(args.account_id, args.profiles)
            elif args.action == "list":
                self._list_mappings()
            elif args.action == "remove":
                self._remove_mapping(args.account_id)

        except TelcoCLIException:
            raise
        except KeyboardInterrupt:
            logger.info("Operation cancelled by user")
            raise TelcoCLIException(ErrorCode.USER_CANCELLED, "Operation cancelled by user")
        except Exception as e:
            logger.exception("Unexpected error during credential configuration")
            raise TelcoCLIException(ErrorCode.CREDENTIAL_PARSE_ERROR, str(e))

    def _load_mappings(self) -> dict:
        """Load account mappings from config file."""
        config_file = Path.home() / ".aws" / "account_mappings.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        logger.warning("Invalid mappings file format, using empty mappings")
                        return {}
                    return data
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Failed to parse mappings file: {e}")
                return {}
            except (OSError, PermissionError) as e:
                logger.error(f"Failed to read mappings file: {e}")
                return {}
        return {}

    def _save_mappings(self, mappings: dict) -> None:
        """Save mappings to config file."""
        try:
            config_file = Path.home() / ".aws" / "account_mappings.json"
            config_file.parent.mkdir(exist_ok=True)
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(mappings, f, indent=2)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to save mappings: {e}")
            raise TelcoCLIException(
                ErrorCode.CREDENTIAL_PARSE_ERROR, f"Could not save credential mappings: {e}"
            )
        except Exception as e:
            logger.exception("Unexpected error saving mappings")
            raise TelcoCLIException(
                ErrorCode.CREDENTIAL_PARSE_ERROR, f"Failed to save credential mappings: {e}"
            )

    def _add_mapping(self, account_id: str, profiles_str: str) -> None:
        """Add account to profile mapping."""
        # Validate inputs
        if not account_id or not account_id.strip():
            raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Account ID cannot be empty")
        if not profiles_str or not profiles_str.strip():
            raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Profiles cannot be empty")

        # Sanitize account ID (AWS account IDs are 12 digits)
        account_id = account_id.strip()
        if not account_id.isdigit() or len(account_id) != 12:
            raise TelcoCLIException(
                ErrorCode.VALIDATION_ERROR, "Account ID must be exactly 12 digits"
            )

        mappings = self._load_mappings()
        profiles = [p.strip() for p in profiles_str.split(",") if p.strip()]

        if not profiles:
            raise TelcoCLIException(
                ErrorCode.VALIDATION_ERROR, "At least one valid profile must be specified"
            )

        logger.info(f"Adding mapping for account {account_id} to profiles: {profiles}")

        mappings[account_id] = profiles
        self._save_mappings(mappings)

        console.print(f"✅ [green]Added mapping:[/green] {account_id} -> {', '.join(profiles)}")

    def _list_mappings(self) -> None:
        """List all configured mappings."""
        mappings = self._load_mappings()

        if not mappings:
            console.print("📭 [yellow]No account mappings configured[/yellow]")
            console.print("\nTo add a mapping, use:")
            console.print(
                "  [cyan]telcocli configure-credentials add <account-id> <profile1,profile2>[/cyan]"
            )
        else:
            console.print("🔗 [bold cyan]AWS Account -> Profile Mappings:[/bold cyan]")
            console.print()
            for account_id, profiles in mappings.items():
                console.print(f"  [cyan]{account_id}[/cyan]: {', '.join(profiles)}")
            console.print(f"\nTotal: {len(mappings)} account mappings configured")

    def _remove_mapping(self, account_id: str) -> None:
        """Remove account mapping."""
        # Validate input
        if not account_id or not account_id.strip():
            raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Account ID cannot be empty")

        account_id = account_id.strip()
        if not account_id.isdigit() or len(account_id) != 12:
            raise TelcoCLIException(
                ErrorCode.VALIDATION_ERROR, "Account ID must be exactly 12 digits"
            )

        mappings = self._load_mappings()

        if account_id in mappings:
            removed_profiles = mappings[account_id]
            logger.info(f"Removing mapping for account {account_id} (profiles: {removed_profiles})")

            del mappings[account_id]
            self._save_mappings(mappings)

            console.print(f"✅ [green]Removed mapping for account[/green] {account_id}")
        else:
            logger.warning(f"No mapping found for account {account_id}")
            console_error.print(f"[red]No mapping found for account[/red] {account_id}")
            console.print("\nTo see existing mappings, use:")
            console.print("  [cyan]telcocli configure-credentials list[/cyan]")
