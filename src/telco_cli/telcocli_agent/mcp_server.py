# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""MCP server implementation for TelcoCLI agent."""

import asyncio
import json
import sys
from typing import Any, Dict

from .agent import TelcoCLIAgent

try:
    from telco_cli.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class TelcoCLIMCPServer:
    """MCP server exposing TelcoCLI agent capabilities."""

    def __init__(self):
        self.agent = TelcoCLIAgent()
        self.tools = self._register_mcp_tools()

    def _register_mcp_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register TelcoCLI tools for MCP exposure."""
        return {
            "telco_ask": {
                "name": "telco_ask",
                "description": "Ask TelcoCLI AI assistant with natural language",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query for TelcoCLI operations",
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Optional session ID for conversation continuity",
                        },
                    },
                    "required": ["query"],
                },
            },
            "telco_execute": {
                "name": "telco_execute",
                "description": "Execute TelcoCLI commands with confirmation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "TelcoCLI command to execute"},
                        "purpose": {
                            "type": "string",
                            "description": "Purpose description for the command",
                        },
                    },
                    "required": ["command", "purpose"],
                },
            },
            "telco_search": {
                "name": "telco_search",
                "description": "Search TelcoCLI commands and documentation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for commands or topics",
                        }
                    },
                    "required": ["query"],
                },
            },
        }

    async def handle_list_tools(self) -> Dict[str, Any]:
        """Handle MCP list_tools request."""
        return {"tools": list(self.tools.values())}

    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP call_tool request."""
        try:
            if name == "telco_ask":
                response = self.agent.ask(arguments["query"], arguments.get("session_id"))
                return {"content": [{"type": "text", "text": response}]}

            elif name == "telco_execute":
                from .executor import execute_command_with_confirmation

                success, output = execute_command_with_confirmation(
                    arguments["command"], arguments["purpose"]
                )

                result = f"{'✅ Success' if success else '❌ Failed'}:\n{output}"
                return {"content": [{"type": "text", "text": result}]}

            elif name == "telco_search":
                from .tools import search_commands_tool

                result = search_commands_tool(arguments["query"])
                return {"content": [{"type": "text", "text": result}]}

            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                    "isError": True,
                }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return await self.handle_list_tools()
        elif method == "tools/call":
            return await self.handle_call_tool(params.get("name"), params.get("arguments", {}))
        else:
            return {"error": {"code": -32601, "message": f"Method not found: {method}"}}

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting TelcoCLI MCP Server")

        loop = asyncio.get_running_loop()

        try:
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)

                if not line:
                    break

                try:
                    request = json.loads(line.strip())
                    response = await self.handle_request(request)

                    if "id" in request:
                        response["id"] = request["id"]

                    print(json.dumps(response))
                    sys.stdout.flush()

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Request failed: {e}")

        except KeyboardInterrupt:
            logger.info("MCP Server stopped")
        finally:
            # Cleanup resources
            logger.info("Cleaning up MCP Server resources")


async def main():
    """Main entry point for MCP server."""
    server = None
    try:
        server = TelcoCLIMCPServer()
        await server.run()
    finally:
        if server:
            # Cleanup server resources if needed
            logger.info("MCP Server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
