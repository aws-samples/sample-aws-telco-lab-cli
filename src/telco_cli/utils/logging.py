# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Logging configuration for TelcoCLI."""

import logging
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

TELCO_THEME = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "highlight": "bold cyan",
        "progress": "dim cyan",
    }
)

SUPPRESSED_LOGGERS = [
    "boto3",
    "botocore",
    "urllib3",
]

FILE_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global console instance for user-facing output
console = Console(theme=TELCO_THEME)

# Error console that always writes to stderr
console_error = Console(stderr=True, theme=TELCO_THEME)


def setup_logging(
    verbose: bool = False, quiet: bool = False, log_file: Optional[Path] = None
) -> None:
    """
    Configure logging based on verbosity flags.

    Args:
        verbose: Enable debug logging
        quiet: Suppress info level logs (only show warnings/errors)
        log_file: Optional file path to write logs
    """

    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.WARNING
    else:
        level = logging.INFO

    handlers: List[logging.Handler] = []

    # Console handler for stderr (technical logs)
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=verbose,
        show_path=verbose,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
    )
    console_handler.setLevel(level)
    handlers.append(console_handler)

    # File handler if requested
    # TODO: Move to Cloudwatch logs
    if log_file:
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter(FILE_LOG_FORMAT, FILE_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Set to DEBUG, handlers control actual output
        handlers=handlers,
        format="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not verbose:
        for logger_name in SUPPRESSED_LOGGERS:
            logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name."""
    return logging.getLogger(name)
