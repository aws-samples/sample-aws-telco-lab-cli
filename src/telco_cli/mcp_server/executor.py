# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Command execution for TelcoCLI MCP server."""

import argparse
import asyncio
import io
import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict

from telco_cli.types.base_command import BaseCommand


async def execute_command(
    command_name: str, arguments: Dict[str, Any], command: BaseCommand
) -> str:
    """Execute a TelcoCLI command safely and return output.

    Args:
        command_name: Name of the command to execute
        arguments: Command arguments from MCP call
        command: Command instance to execute

    Returns:
        Command output as string
    """
    # Extract and handle global options
    global_options = {}
    command_args = {}

    for key, value in arguments.items():
        if key in ["profile", "region", "verbose", "quiet"]:
            global_options[key] = value
        else:
            command_args[key] = value

    # Set environment variables for global options
    if "profile" in global_options:
        os.environ["AWS_PROFILE"] = global_options["profile"]
    if "region" in global_options:
        os.environ["AWS_DEFAULT_REGION"] = global_options["region"]

    # Create a temporary parser to get default values
    temp_parser = argparse.ArgumentParser()
    command.register(temp_parser)

    # Parse empty args to get defaults
    default_args = temp_parser.parse_args([])

    # Convert MCP arguments to argparse Namespace, starting with defaults
    args_namespace = argparse.Namespace(**vars(default_args))

    # Override with provided command arguments
    for key, value in command_args.items():
        # Handle list arguments (nargs='*' or '+')
        if isinstance(value, list):
            setattr(args_namespace, key, value)
        else:
            setattr(args_namespace, key, value)

    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        # Execute command in captured context
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Run the command
            await asyncio.get_event_loop().run_in_executor(None, command.run, args_namespace)

        # Get captured output
        stdout_content = stdout_capture.getvalue()
        stderr_content = stderr_capture.getvalue()

        # Combine outputs
        result = ""
        if stdout_content:
            result += f"Output:\n{stdout_content}\n"
        if stderr_content:
            result += f"Errors:\n{stderr_content}\n"

        return result if result else "Command executed successfully (no output)"

    except Exception as e:
        error_output = stderr_capture.getvalue()
        return f"Command failed: {str(e)}\n{error_output if error_output else ''}"
