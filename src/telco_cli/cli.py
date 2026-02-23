# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Main CLI entry point for TelcoCLI."""

import argparse
import importlib
import os
import pkgutil
import sys
from pathlib import Path
from typing import List

import telco_cli.commands
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console_error, get_logger, setup_logging
from telco_cli.utils.constants import (
    ACTION_STORE_TRUE,
    ACTION_VERSION,
    ARG_COMMAND,
    ARG_LOG_FILE,
    ARG_QUIET,
    ARG_QUIET_SHORT,
    ARG_VERBOSE,
    ARG_VERBOSE_SHORT,
    ARG_VERSION,
    ERROR_NO_COMMANDS,
    ERROR_UNEXPECTED,
    ERROR_VERBOSE_QUIET_CONFLICT,
    HELP_COMMANDS,
    HELP_LOG_FILE,
    HELP_QUIET,
    HELP_VERBOSE,
    LOG_ARGUMENTS,
    LOG_CANCELLED,
    LOG_CLI_STARTED,
    LOG_EXECUTING_COMMAND,
    LOG_UNEXPECTED_ERROR,
    PROG_DESCRIPTION,
    PROG_NAME,
    PROG_VERSION,
    WARNING_CANCELLED,
    WARNING_IMPORT_FAILED,
)

logger = get_logger(__name__)


def discover_commands() -> List[BaseCommand]:
    """Auto-discovers all commands in the commands package."""
    commands = []
    for _, module_name, _ in pkgutil.iter_modules(telco_cli.commands.__path__):
        try:
            module = importlib.import_module(f"telco_cli.commands.{module_name}")
            for obj in vars(module).values():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseCommand)
                    and obj is not BaseCommand
                ):
                    commands.append(obj())
        except ImportError as e:
            logger.warning(WARNING_IMPORT_FAILED.format(module=module_name, error=e))

    return commands


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=PROG_DESCRIPTION,
        epilog=(
            "SECURITY NOTICE: This is sample code for demonstration purposes. "
            "Review IAM policies, security groups, and configurations before production use. "
            "Never hardcode credentials. See SECURITY.md for details."
        ),
    )

    # Global arguments
    parser.add_argument(ARG_VERSION, action=ACTION_VERSION, version=PROG_VERSION)
    parser.add_argument(ARG_VERBOSE, ARG_VERBOSE_SHORT, action=ACTION_STORE_TRUE, help=HELP_VERBOSE)
    parser.add_argument(
        ARG_QUIET,
        ARG_QUIET_SHORT,
        action=ACTION_STORE_TRUE,
        help=HELP_QUIET,
    )
    parser.add_argument("--profile", help="AWS CLI profile to use for this command (optional)")
    parser.add_argument("--region", help="AWS region to use for this command (optional)")
    parser.add_argument(ARG_LOG_FILE, type=Path, help=HELP_LOG_FILE)

    subparsers = parser.add_subparsers(dest=ARG_COMMAND, required=False, help=HELP_COMMANDS)

    commands = discover_commands()

    if not commands:
        console_error.print(ERROR_NO_COMMANDS)
        sys.exit(1)

    for command in commands:
        subparser = subparsers.add_parser(
            command.name, description=command.description, help=command.description
        )
        command.register(subparser)
        subparser.set_defaults(_run=command.run)

    args = parser.parse_args()

    if args.verbose and args.quiet:
        console_error.print(ERROR_VERBOSE_QUIET_CONFLICT)
        sys.exit(1)

    setup_logging(verbose=args.verbose, quiet=args.quiet, log_file=args.log_file)

    logger.debug(LOG_CLI_STARTED.format(command=args.command))
    logger.debug(LOG_ARGUMENTS.format(args=args))

    # Default to help if no command is provided
    if args.command is None:
        parser.print_help()
        return

    try:
        # Set AWS profile and region if provided
        if hasattr(args, "profile") and args.profile:
            os.environ["AWS_PROFILE"] = args.profile
        if hasattr(args, "region") and args.region:
            os.environ["AWS_DEFAULT_REGION"] = args.region

        logger.info(LOG_EXECUTING_COMMAND.format(command=args.command))
        args._run(args)
    except KeyboardInterrupt:
        console_error.print(WARNING_CANCELLED)
        logger.info(LOG_CANCELLED)
        sys.exit(1)
    except Exception as e:
        console_error.print(ERROR_UNEXPECTED.format(error=e))
        logger.exception(LOG_UNEXPECTED_ERROR)
        sys.exit(1)


if __name__ == "__main__":
    main()
