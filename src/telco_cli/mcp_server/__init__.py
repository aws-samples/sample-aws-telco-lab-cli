# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""TelcoCLI MCP Server package."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import CallToolResult, TextContent, Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None  # type: ignore
    stdio_server = None  # type: ignore
    CallToolResult = None  # type: ignore
    TextContent = None  # type: ignore
    Tool = None  # type: ignore

from telco_cli.cli import discover_commands

from .executor import execute_command
from .schema_generator import generate_tool_schema

# Set up logging to file for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/tmp/telcocli-mcp.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize MCP server only if available
server: Optional[Any] = None
commands: Dict[str, Any] = {}

if MCP_AVAILABLE:
    server = Server("telcocli-mcp")
    commands = {cmd.name: cmd for cmd in discover_commands()}
    logger.info(f"Discovered {len(commands)} TelcoCLI commands")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        """List all available TelcoCLI tools."""
        tools = []
        for name, command in commands.items():
            tool_name = f"telcocli_{name.replace('-', '_')}"
            tools.append(
                Tool(
                    name=tool_name,
                    description=command.description,
                    inputSchema=generate_tool_schema(command),
                )
            )
        logger.debug(f"Returning {len(tools)} tools")
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Execute a TelcoCLI command."""
        try:
            # Convert tool name back to command name
            command_name = name.replace("telcocli_", "").replace("_", "-")

            if command_name not in commands:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown command: {command_name}")],
                    isError=True,
                )

            # Execute the command
            result = await execute_command(command_name, arguments, commands[command_name])

            return CallToolResult(content=[TextContent(type="text", text=result)])

        except Exception as e:
            logger.exception(f"Error executing command {name}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error executing {name}: {str(e)}")],
                isError=True,
            )


async def main():
    """Main entry point for TelcoCLI MCP server."""
    if not MCP_AVAILABLE:
        logger.error("MCP module not available. Install with: pip install mcp")
        return
    
    logger.info("Starting TelcoCLI MCP Server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
