# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Knowledge base loader - loads and provides access to command documentation."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_knowledge_base() -> Dict[str, Any]:
    """Load the knowledge base from JSON file.

    Returns:
        Dictionary containing command documentation.
    """
    kb_path = Path(__file__).parent / "commands.json"

    if not kb_path.exists():
        # If KB doesn't exist, build it from documentation
        from .doc_builder import DocumentationKnowledgeBaseBuilder

        builder = DocumentationKnowledgeBaseBuilder()
        kb = builder.build()
        builder.save()
        return kb

    with open(kb_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_aws_errors() -> Dict[str, Any]:
    """Load AWS errors knowledge base.

    Returns:
        Dictionary containing AWS error documentation.
    """
    errors_path = Path(__file__).parent / "aws_errors.json"

    if not errors_path.exists():
        return {}

    with open(errors_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_commands(kb: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
    """Search for commands matching a query.

    Args:
        kb: Knowledge base dictionary.
        query: Search query string.

    Returns:
        List of matching command dictionaries.
    """
    query_lower = query.lower()
    results = []

    for cmd_name, cmd_info in kb.get("commands", {}).items():
        # Search in name, description, and category
        if (
            query_lower in cmd_name.lower()
            or query_lower in cmd_info.get("description", "").lower()
            or query_lower in cmd_info.get("category", "").lower()
        ):
            results.append(cmd_info)

    return results


def get_command_info(kb: Dict[str, Any], command_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific command.

    Args:
        kb: Knowledge base dictionary.
        command_name: Name of the command.

    Returns:
        Command information dictionary or None if not found.
    """
    return kb.get("commands", {}).get(command_name)


def get_commands_by_category(kb: Dict[str, Any], category: str) -> List[str]:
    """Get all commands in a specific category.

    Args:
        kb: Knowledge base dictionary.
        category: Category name.

    Returns:
        List of command names in the category.
    """
    return kb.get("categories", {}).get(category, [])


def format_command_help(cmd_info: Dict[str, Any]) -> str:
    """Format command information as help text.

    Args:
        cmd_info: Command information dictionary.

    Returns:
        Formatted help text.
    """
    lines = []
    lines.append(f"Command: telcocli {cmd_info['name']}")
    lines.append(f"Description: {cmd_info['description']}")
    lines.append("")

    if cmd_info.get("parameters"):
        lines.append("Parameters:")
        for param in cmd_info["parameters"]:
            required = " (required)" if param.get("required") else " (optional)"
            lines.append(f"  {param['name']}{required}")
            if param.get("help"):
                lines.append(f"    {param['help']}")
        lines.append("")

    lines.append(f"Category: {cmd_info.get('category', 'general')}")

    if cmd_info.get("docstring"):
        lines.append("")
        lines.append("Additional Information:")
        lines.append(cmd_info["docstring"])

    return "\n".join(lines)
