# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Base exception class for the Telco CLI."""

import logging
from typing import Optional

from telco_cli.exceptions.error_codes import ErrorCode

logger = logging.getLogger(__name__)


class TelcoCLIException(Exception):
    """Generic TelcoCLI error with code + exit code."""

    exit_code: int = 1

    def __init__(
        self, error_code: ErrorCode, message: str, *params, exit_code: Optional[int] = None
    ):
        """Initialize the CLI error.

        Args:
            error_code: The specific error code for this error
            message: The error message (can contain {} placeholders)
            *params: Parameters to format into the message
            exit_code: Optional exit code override
        """
        if params:
            try:
                message = message.format(*params)
            except Exception:
                logger.exception(
                    "Failed to format exception message: '%s' with params %s",
                    message,
                    params,
                )

        super().__init__(message)
        self.error_code = error_code

        # Use the error code's value as exit code if not explicitly provided
        if exit_code is not None:
            self.exit_code = exit_code
        else:
            self.exit_code = int(error_code)

    def __str__(self) -> str:
        """Return the string representation with error code name + number."""
        return f"[{self.error_code.name} - {self.error_code.value}] {super().__str__()}"
