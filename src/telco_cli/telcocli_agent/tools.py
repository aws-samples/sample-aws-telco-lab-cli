# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Custom tools for TelcoCLI agent."""

import html
import re
from typing import Any, Dict, List

from strands import tool

from .knowledge_base.fast_loader import (
    format_command_help,
    get_command_info,
    load_aws_errors_fast,
    load_knowledge_base_fast,
    search_commands,
)

# Pre-load knowledge bases at module level for maximum performance
_KB = load_knowledge_base_fast()
_AWS_ERRORS = load_aws_errors_fast()


def _get_kb() -> Dict[str, Any]:
    """Get cached knowledge base."""
    return _KB


def _get_aws_errors() -> Dict[str, Any]:
    """Get cached AWS errors knowledge base."""
    return _AWS_ERRORS


@tool
def get_command_info_tool(command_name: str) -> str:
    """Get detailed information about a specific TelcoCLI command.

    Use this tool when the user asks about a specific command, wants to know
    how to use a command, or needs details about command parameters.

    Args:
        command_name: The name of the TelcoCLI command (e.g., "list-partners", "create-vpn")

    Returns:
        Formatted help text with command details, parameters, and usage information.

    Examples:
        - User asks: "How do I use the list-partners command?"
        - User asks: "What parameters does create-vpn take?"
        - User asks: "Tell me about the analyze-dedicated-hosts command"
    """
    kb = _get_kb()
    cmd_info = get_command_info(kb, command_name)

    if not cmd_info:
        # Try to find similar commands
        similar = search_commands(kb, command_name)
        if similar:
            suggestions = ", ".join([html.escape(cmd["name"]) for cmd in similar[:3]])
            return f"Command '{html.escape(command_name)}' not found. Did you mean: {suggestions}?"
        return f"Command '{html.escape(command_name)}' not found in TelcoCLI."

    help_text = format_command_help(cmd_info)

    # Add example usage
    help_text += "\n\nExample Usage:"
    help_text += f"\n  telcocli {cmd_info['name']}"

    # Add common parameters if they exist
    if cmd_info.get("parameters"):
        required_params = [p for p in cmd_info["parameters"] if p.get("required")]
        if required_params:
            param_example = " ".join(
                [f"--{p['name'].lstrip('-')} <value>" for p in required_params[:2]]
            )
            help_text += f" {param_example}"

    # Add AWS documentation tag
    help_text += (
        "\n\n[Best Practice] Always verify AWS credentials are configured before running commands."
    )
    help_text += "\n[AWS Official] Use --profile and --region flags to specify AWS configuration."

    return help_text


@tool
def search_commands_tool(query: str) -> str:
    """MANDATORY FIRST STEP: Search TelcoCLI knowledge base before using any other tools.

    This tool MUST be used first for ANY user request to check if TelcoCLI has a specialized command.
    TelcoCLI has 21 specialized commands that should be preferred over AWS CLI.

    Args:
        query: Any keywords from the user's request (e.g., "test servers", "outposts", "partners", "vpn")

    Returns:
        List of matching TelcoCLI commands with descriptions.

    ALWAYS use this tool first, even for specific requests like:
        - "list test servers" → search for "test servers"
        - "get outpost details" → search for "outpost"
        - "create VPN certificate" → search for "vpn"
    """
    kb = _get_kb()
    results = search_commands(kb, query)

    if not results:
        return f"No commands found matching '{html.escape(query)}'. Try a different search term or ask about available categories."

    # Format results
    output = [f"Found {len(results)} command(s) matching '{html.escape(query)}':\n"]

    for i, cmd in enumerate(results[:10], 1):  # Limit to top 10 results
        output.append(f"{i}. telcocli {html.escape(cmd['name'])}")
        output.append(f"   {html.escape(cmd['description'])}")
        output.append(f"   Category: {html.escape(cmd.get('category', 'general'))}")
        output.append("")

    if len(results) > 10:
        output.append(f"... and {len(results) - 10} more commands.")
        output.append("Refine your search for more specific results.")

    output.append(
        "\n[Best Practice] Use get_command_info_tool to get detailed information about a specific command."
    )

    return "\n".join(output)


@tool
def execute_command_tool(command: str, purpose: str) -> str:
    """Execute a TelcoCLI or AWS CLI command with user confirmation.

    Use this tool when the user wants to actually run a command, not just see it.
    This will prompt the user for confirmation before executing.

    Args:
        command: The exact command to execute
        purpose: Brief description of what the command does

    Returns:
        The command output or error message.

    Examples:
        - command: "telcocli --profile my-profile list-outposts --output table"
        - purpose: "List all outposts using my-profile profile"
    """
    try:
        from .executor import execute_command_with_confirmation

        success, output = execute_command_with_confirmation(command, purpose)

        if success:
            return f"Command executed successfully:\n{output}"
        else:
            return f"Command failed:\n{output}"
    except ImportError:
        return "Error: Command execution not available"


@tool
def generate_command_tool(user_request: str) -> str:
    """Generate the exact TelcoCLI or AWS CLI command for a user request.

    Use this tool when the user asks for a specific operation or wants to accomplish
    a task. This tool will provide the exact command to run.

    Args:
        user_request: The user's request describing what they want to do

    Returns:
        The exact command to execute with proper syntax and parameters.

    Examples:
        - User asks: "list outposts in my-profile profile"
        - User asks: "get details of all partners"
        - User asks: "create VPN for partner acme"
    """
    kb = _get_kb()

    # Parse the request to identify:
    # 1. Action (list, get, create, etc.)
    # 2. Resource (outposts, partners, vpn, etc.)
    # 3. Profile/region mentioned
    # 4. Additional parameters

    request_lower = user_request.lower()

    # Extract profile if mentioned
    profile_match = re.search(r"(?:profile|account)\s+(\S+)", request_lower)
    profile = f" --profile {profile_match.group(1)}" if profile_match else ""

    # Extract region if mentioned
    region_match = re.search(r"(?:region|in)\s+(us-[\w-]+|eu-[\w-]+|ap-[\w-]+)", request_lower)
    region = f" --region {region_match.group(1)}" if region_match else ""

    # Map common requests to commands
    if "list" in request_lower and "outpost" in request_lower:
        return f"```bash\n# List all outposts{profile and ' using' + profile or ''}\ntelcocli{profile} list-outposts --output table\n```"

    elif "detail" in request_lower and "outpost" in request_lower:
        return f"```bash\n# Get detailed outpost information{profile and ' using' + profile or ''}\ntelcocli{profile} get-outpost-utilization-summary --include-details --output table\n```"

    elif "list" in request_lower and "partner" in request_lower:
        return f"```bash\n# List all partners{profile and ' using' + profile or ''}\ntelcocli{profile} list-partners --output table\n```"

    elif "create" in request_lower and "vpn" in request_lower:
        partner_match = re.search(r"(?:partner|for)\s+(\w+)", request_lower)
        partner = partner_match.group(1) if partner_match else "PARTNER_NAME"
        return f"```bash\n# Create VPN certificate for {partner}{profile and ' using' + profile or ''}\ntelcocli{profile} create-vpn {partner} --allowed-subnets \"10.0.0.0/16\"\n```"

    elif "list" in request_lower and "vpn" in request_lower:
        return f"```bash\n# List VPN certificates{profile and ' using' + profile or ''}\ntelcocli{profile} list-vpn-certificates --show-details --output table\n```"

    elif "dedicated" in request_lower and "host" in request_lower:
        if "analyze" in request_lower or "list" in request_lower:
            return f"```bash\n# Analyze dedicated hosts{profile and ' using' + profile or ''}\ntelcocli{profile} analyze-dedicated-hosts --format table\n```"

    elif "eks" in request_lower or "kubernetes" in request_lower:
        if "deploy" in request_lower or "create" in request_lower:
            cluster_match = re.search(r"(?:cluster|named?)\s+(\w+)", request_lower)
            cluster = cluster_match.group(1) if cluster_match else "my-cluster"
            return f"```bash\n# Deploy EKS cluster{profile and ' using' + profile or ''}\ntelcocli{profile} deploy-eks-full --cluster-name {cluster} --deploy-vpc --deploy-eks --deploy-worker-nodes\n```"

    elif "s3" in request_lower:
        if "list" in request_lower and "bucket" in request_lower:
            return f"```bash\n# AWS CLI alternative (TelcoCLI doesn't support S3)\naws{profile}{region} s3 ls\n```"
        elif "create" in request_lower and "bucket" in request_lower:
            bucket_match = re.search(r"bucket\s+(\S+)", request_lower)
            bucket = bucket_match.group(1) if bucket_match else "my-bucket"
            return f"```bash\n# AWS CLI alternative (TelcoCLI doesn't support S3)\naws{profile}{region} s3 mb s3://{bucket}\n```"

    elif "ec2" in request_lower:
        if "list" in request_lower and "instance" in request_lower:
            return f"```bash\n# AWS CLI alternative (TelcoCLI doesn't support EC2 instances directly)\naws{profile}{region} ec2 describe-instances --output table\n```"

    elif "iam" in request_lower:
        if "list" in request_lower and "user" in request_lower:
            return f"```bash\n# AWS CLI alternative (TelcoCLI doesn't support IAM)\naws{profile} iam list-users --output table\n```"

    # Default fallback - search for relevant commands
    results = search_commands(kb, user_request)
    if results:
        cmd = results[0]
        return f"```bash\n# {cmd['description']}\ntelcocli{profile} {cmd['name']} --help\n```\n\nUse --help to see all available options for this command."

    return "```bash\n# No specific TelcoCLI command found. Try:\ntelcocli --help\n```\n\nOr use AWS CLI for operations TelcoCLI doesn't support."


@tool
def explain_aws_error_tool(error_code: str) -> str:
    """Explain an AWS error code and provide troubleshooting steps.

    Use this tool when the user encounters an AWS error and needs help understanding
    what went wrong and how to fix it.

    Args:
        error_code: The AWS error code (e.g., "AccessDenied", "InvalidParameterValue",
                   "ResourceNotFound", "ThrottlingException")

    Returns:
        Explanation of the error, common causes, and step-by-step solutions.

    Examples:
        - User says: "I got an AccessDenied error"
        - User asks: "What does InvalidParameterValue mean?"
        - User reports: "The command failed with ResourceNotFound"
    """
    aws_errors = _get_aws_errors()

    # Normalize and sanitize error code (remove common prefixes/suffixes)
    error_code_normalized = (
        html.escape(error_code).replace("Exception", "").replace("Error", "").strip()
    )

    error_info = aws_errors.get(error_code_normalized) or aws_errors.get(error_code)

    if not error_info:
        # Provide generic guidance
        output = [f"Error: {html.escape(error_code)}"]
        output.append("\n[Best Practice] General AWS Error Troubleshooting Steps:")
        output.append("1. Check the full error message for specific details")
        output.append("2. Verify your AWS credentials are valid and not expired")
        output.append("3. Confirm you're using the correct AWS region with --region")
        output.append("4. Check IAM permissions for the operation you're trying to perform")
        output.append("5. Review AWS CloudTrail logs for more details")
        output.append(
            "\n[AWS Official] AWS Error Reference: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html"
        )

        # Suggest alternative AWS CLI command
        output.append(
            "\n[Alternative] If TelcoCLI doesn't support this operation, try the AWS CLI:"
        )
        output.append("  aws <service> <operation> --help")

        return "\n".join(output)

    # Format detailed error information
    output = [f"[AWS Official] Error: {html.escape(error_code)}"]
    output.append(f"\nDescription: {html.escape(error_info['description'])}")

    output.append("\nCommon Causes:")
    for i, cause in enumerate(error_info.get("common_causes", []), 1):
        output.append(f"  {i}. {html.escape(cause)}")

    output.append("\n[Best Practice] Troubleshooting Steps:")
    for i, solution in enumerate(error_info.get("solutions", []), 1):
        output.append(f"  {i}. {html.escape(solution)}")

    if error_info.get("aws_docs"):
        output.append(f"\n[AWS Official] Documentation: {error_info['aws_docs']}")

    # Add preventive measures
    output.append("\n[Best Practice] Prevention:")
    output.append("  - Always test commands in a non-production environment first")
    output.append("  - Use --dry-run flag when available")
    output.append("  - Keep AWS credentials and permissions up to date")

    # Suggest AWS CLI alternative
    output.append("\n[Alternative] If TelcoCLI cannot resolve this, try AWS CLI:")
    output.append("  aws sts get-caller-identity  # Verify credentials")
    output.append("  aws <service> help  # Get service-specific help")

    return "\n".join(output)


def get_all_tools() -> List:
    """Get all TelcoCLI tools for the agent.

    Returns:
        List of tool functions.
    """
    return [
        execute_command_tool,
        generate_command_tool,
        get_command_info_tool,
        search_commands_tool,
        explain_aws_error_tool,
    ]
