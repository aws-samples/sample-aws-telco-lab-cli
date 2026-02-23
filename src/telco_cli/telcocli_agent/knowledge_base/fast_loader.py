# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Fast knowledge base loader using pre-compiled cache."""

from typing import Any, Dict, List

try:
    # Try to import pre-compiled cache first
    from .commands_cache import AWS_ERRORS, COMMANDS

    _USE_CACHE = True
except ImportError:
    # Fallback to JSON loading
    _USE_CACHE = False


def load_knowledge_base_fast() -> Dict[str, Any]:
    """Load knowledge base with caching optimization.

    Returns:
        Dictionary containing command documentation.
    """
    if _USE_CACHE:
        return COMMANDS
    else:
        # Fallback to original JSON loader
        from .loader import load_knowledge_base

        return load_knowledge_base()


def load_aws_errors_fast() -> Dict[str, Any]:
    """Load AWS errors with caching optimization.

    Returns:
        Dictionary containing AWS error information.
    """
    if _USE_CACHE:
        return AWS_ERRORS
    else:
        # Fallback to original JSON loader
        from .loader import load_aws_errors

        return load_aws_errors()


# Compatibility functions
def search_commands(kb: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """Search commands by query string."""
    results = []
    query_lower = query.lower()

    for cmd_name, cmd_info in kb.items():
        if (
            query_lower in cmd_name.lower()
            or query_lower in cmd_info.get("description", "").lower()
            or query_lower in cmd_info.get("category", "").lower()
        ):
            results.append(cmd_info)

    return results


def get_command_info(kb: Dict[str, Any], command_name: str) -> Dict[str, Any]:
    """Get specific command information."""
    return kb.get(command_name, {})


def format_command_help(cmd_info: Dict[str, Any]) -> str:
    """Format command information as help text."""
    if not cmd_info:
        return "Command not found."

    help_text = f"Command: telcocli {cmd_info['name']}\n"
    help_text += f"Description: {cmd_info.get('description', 'No description')}\n"

    if cmd_info.get("parameters"):
        help_text += "\nParameters:\n"
        for param in cmd_info["parameters"]:
            required = " (required)" if param.get("required") else " (optional)"
            help_text += f"  {param['name']}{required}\n"
            if param.get("help"):
                help_text += f"    {param['help']}\n"

    if cmd_info.get("examples"):
        help_text += "\nExamples:\n"
        for example in cmd_info["examples"]:
            help_text += f"  {example}\n"

    return help_text
