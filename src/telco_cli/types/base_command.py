# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import argparse
import logging
import subprocess
from abc import ABC, abstractmethod
from typing import List

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.utils.logging import console_error

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """Abstract base class for all TelcoCLI commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Subcommand name (e.g., 'help', 'ec2')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description for argparse help text."""
        pass

    @abstractmethod
    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register argparse arguments for this command."""
        pass

    @abstractmethod
    def run(self, args: argparse.Namespace) -> None:
        """Main logic to execute the command."""
        pass

    def _execute(self, command: List[str]) -> None:
        """
        Execute the subprocess command with consistent error handling.

        SECURITY: Uses shell=False and list-based commands to prevent injection.
        """
        try:
            logger.debug("Executing command: %s", " ".join(command))
            # SECURITY: shell=False prevents command injection
            # timeout prevents indefinite hanging
            subprocess.run(command, shell=False, check=True, timeout=300)
        except subprocess.TimeoutExpired as e:
            console_error.print("❌ Command timed out after 5 minutes", style="error")
            raise TelcoCLIException(
                ErrorCode.COMMAND_EXECUTION_ERROR, f"Command timed out: {e}"
            ) from e
        except subprocess.CalledProcessError as e:
            console_error.print("❌ Error executing system command", style="error")
            raise TelcoCLIException(
                ErrorCode.COMMAND_EXECUTION_ERROR, f"Command failed: {e}"
            ) from e
        except FileNotFoundError as e:
            console_error.print("❌ CLI tool not found", style="error")
            raise TelcoCLIException(ErrorCode.COMMAND_EXECUTION_ERROR, "CLI tool not found") from e
        except TelcoCLIException:
            raise  # don’t double-wrap our own errors
        except Exception as e:
            logger.exception("Unexpected error in command execution")
            raise TelcoCLIException(ErrorCode.UNKNOWN_ERROR, f"Unexpected error: {e}") from e
