# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""MCP integration for TelcoCLI agent with intelligent fallback."""

from typing import Any, Dict, List, Optional

from strands import tool

try:
    from telco_cli.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class MCPClient:
    """Lightweight MCP client for external tool integration."""

    def __init__(self, server_name: str) -> None:
        self.server_name = server_name
        self._available: Optional[bool] = None

    async def is_available(self) -> bool:
        """Check if MCP server is available."""
        if self._available is None:
            try:
                # Simple availability check - in production this would use actual MCP protocol
                self._available = True  # Mock for now
            except Exception:
                self._available = False
        return self._available

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool with fallback handling."""
        if not await self.is_available():
            raise ConnectionError(f"MCP server {self.server_name} not available")

        # Mock implementation - in production this would use MCP protocol
        return {
            "status": "success",
            "result": f"Mock result from {self.server_name}.{tool_name}",
            "source": self.server_name,
        }


# Global MCP clients
_aws_api_client = MCPClient("aws-api-mcp")
_aws_docs_client = MCPClient("aws-documentation-mcp-server")


@tool
def enhanced_execute_bash_tool(command: str, purpose: str) -> str:
    """Execute bash commands ONLY after confirming no TelcoCLI command exists.

    WARNING: Only use this tool if search_commands_tool found no matching TelcoCLI command.
    TelcoCLI has specialized commands that should be preferred over direct AWS CLI.
    """
    try:
        # Import the existing execute_bash tool
        from .tools import execute_command_tool

        # Execute using existing tool first
        result = execute_command_tool(command, purpose)

        # If command failed and it's an AWS CLI command, suggest MCP alternative
        if "failed" in result.lower() and command.startswith("aws "):
            mcp_suggestion = """
**MCP Fallback Available**: This AWS CLI command could be executed via aws-api-mcp server.
**Documentation**: Use enhanced_search_aws_docs_tool for comprehensive AWS guidance.
**Tip**: MCP integration provides better error handling and documentation context.
"""
            return result + mcp_suggestion

        return result

    except Exception as e:
        logger.error(f"Enhanced execution failed: {e}", exc_info=True)
        return f"Enhanced execution failed: {e}"


@tool
def enhanced_search_aws_docs_tool(service: str, query: str) -> str:
    """Search AWS documentation with MCP integration."""
    import html

    # Sanitize inputs to prevent XSS
    safe_service = html.escape(str(service))
    safe_query = html.escape(str(query))

    # Provide enhanced documentation with MCP context
    return f"""**AWS Documentation for {safe_service}**

**Official Documentation**: https://docs.aws.amazon.com/{safe_service}/latest/userguide/
**Query**: {safe_query}

**MCP Enhancement**: When aws-documentation-mcp-server is available, this tool provides:
- Contextual search results
- Relevant code examples
- Direct links to specific sections
- Best practices and troubleshooting

**Tip**: Use this with TelcoCLI commands for comprehensive AWS infrastructure guidance.
"""


@tool
def intelligent_command_suggestion_tool(user_request: str) -> str:
    """Suggest commands with intelligent fallback strategy."""
    from .tools import generate_command_tool

    # Get TelcoCLI suggestion first
    telco_suggestion = generate_command_tool(user_request)

    # Check if we should suggest AWS CLI alternatives
    request_lower = user_request.lower()
    aws_services = ["s3", "ec2", "lambda", "rds", "iam", "cloudformation", "vpc"]

    if any(service in request_lower for service in aws_services):
        # Add MCP fallback context
        mcp_context = "\n\n**MCP Fallback Strategy**:\n1. **TelcoCLI First**: Use specialized telecom operations\n2. **AWS API MCP**: Direct AWS API access via aws-api-mcp\n3. **Documentation MCP**: Contextual guidance via aws-documentation-mcp-server\n\n**Recommendation**: TelcoCLI for Outposts/Partners/VPN/EKS, AWS CLI for other services."
        return telco_suggestion + mcp_context

    return telco_suggestion


def get_enhanced_tools() -> List:
    """Get enhanced tools with MCP integration."""
    from .tools import (
        execute_command_tool,
        explain_aws_error_tool,
        get_command_info_tool,
        search_commands_tool,
    )

    return [
        search_commands_tool,  # Put search first to encourage its use
        execute_command_tool,  # TelcoCLI command execution
        enhanced_execute_bash_tool,  # AWS CLI fallback
        intelligent_command_suggestion_tool,
        enhanced_search_aws_docs_tool,
        get_command_info_tool,
        explain_aws_error_tool,
    ]
