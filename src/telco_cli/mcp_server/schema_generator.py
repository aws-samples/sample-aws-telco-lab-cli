# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Schema generation for TelcoCLI commands."""

import argparse
from typing import Any, Dict


def generate_tool_schema(command) -> Dict[str, Any]:
    """Generate MCP tool schema from TelcoCLI command.

    Args:
        command: TelcoCLI command instance

    Returns:
        JSON schema for the command
    """
    # Create a temporary parser to extract argument definitions
    temp_parser = argparse.ArgumentParser()
    command.register(temp_parser)

    properties: Dict[str, Any] = {}
    required = []

    # Add global options that apply to all commands
    properties["profile"] = {
        "type": "string",
        "description": "AWS profile name to use for credentials",
    }
    properties["region"] = {
        "type": "string",
        "description": "AWS region to use (e.g., us-east-1, us-west-2)",
    }
    properties["verbose"] = {
        "type": "boolean",
        "description": "Enable verbose output",
    }
    properties["quiet"] = {
        "type": "boolean",
        "description": "Suppress non-essential output",
    }

    # Extract arguments from the parser
    for action in temp_parser._actions:
        if action.dest in ["help", "version"]:
            continue

        arg_name = action.dest
        arg_schema: Dict[str, Any] = {
            "type": "string",  # Default to string
            "description": action.help or f"Argument for {arg_name}",
        }

        # Handle different argument types
        if action.type == int:
            arg_schema["type"] = "integer"
        elif action.type == float:
            arg_schema["type"] = "number"
        elif isinstance(action, argparse._StoreTrueAction) or isinstance(
            action, argparse._StoreFalseAction
        ):
            arg_schema["type"] = "boolean"
        elif action.choices:
            arg_schema["enum"] = list(action.choices)

        # Handle nargs for list arguments
        if action.nargs in ["*", "+"]:
            arg_schema["type"] = "array"
            arg_schema["items"] = {"type": "string"}
            if action.nargs == "+":
                arg_schema["minItems"] = 1

        # Handle positional arguments (required)
        if action.option_strings == []:  # No option strings means positional
            if action.nargs not in ["?", "*"]:  # Not optional
                required.append(arg_name)

        properties[arg_name] = arg_schema

    return {"type": "object", "properties": properties, "required": required}
