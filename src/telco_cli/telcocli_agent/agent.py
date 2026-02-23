# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""TelcoCLI AI Agent - Strands-based assistant for TelcoCLI operations.

This module provides an AI-powered assistant for TelcoCLI that can:
- Generate and execute TelcoCLI commands based on natural language requests
- Provide interactive command execution with user confirmation
- Search and explain TelcoCLI commands and AWS operations
- Maintain conversation sessions for context-aware assistance

The agent integrates with Amazon Bedrock Claude models and follows
TelcoCLI's established patterns for AWS configuration and error handling.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple

from strands import Agent
from strands.models import BedrockModel

# Import TelcoCLI logging utilities
try:
    from telco_cli.utils.logging import get_logger

    logger = get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Try relative imports first, fall back to absolute imports
try:
    from .mcp_integration import get_enhanced_tools
    from .session_manager import SessionManager
    from .tools import get_all_tools
except ImportError:
    from telcocli_agent.mcp_integration import get_enhanced_tools  # type: ignore
    from telcocli_agent.session_manager import SessionManager  # type: ignore
    from telcocli_agent.tools import get_all_tools  # type: ignore


# System prompt that defines the agent's expertise and behavior
TELCOCLI_SYSTEM_PROMPT = """You are a TelcoCLI assistant with comprehensive knowledge of TelcoCLI commands and intelligent AWS fallback capabilities.

🎯 COMMAND SELECTION PRIORITY:
1. **TelcoCLI Commands FIRST**: Always check if a TelcoCLI command exists for the user's request
   - Infrastructure: list-outposts, describe-outpost, analyze-dedicated-hosts, list-test-servers
   - Partners: create-partner, list-partners, describe-partner
   - VPN: create-vpn, list-vpn-certificates, revoke-vpn-certificate
   - EKS: deploy-eks-full, configure-eks-access
   - System: health, start-ssm
2. **AWS CLI Fallback**: Only use AWS CLI when no TelcoCLI command exists
3. **MCP Integration**: Leverage enhanced tools for documentation and complex operations

🔧 TOOL SELECTION WORKFLOW:
1. **search_commands_tool** - ALWAYS search TelcoCLI knowledge base first
2. **execute_command_tool** - Execute TelcoCLI commands when found
3. **enhanced_execute_bash_tool** - Only for AWS CLI when TelcoCLI doesn't have the command
4. **enhanced_search_aws_docs_tool** - For documentation and guidance

📋 MANDATORY DECISION PROCESS:
1. Parse user request to understand the goal
2. **ALWAYS** use search_commands_tool first to check TelcoCLI knowledge base
3. If TelcoCLI command found → Use execute_command_tool with TelcoCLI command
4. If no TelcoCLI command found → Use enhanced_execute_bash_tool with AWS CLI
5. Always provide context and documentation

⚠️ **CRITICAL**: Never skip step 2. Always search TelcoCLI knowledge base before using AWS CLI.

💡 EXAMPLES:
User: "get details of all the test servers that are online in 5g-val profile in us-west-2 include nic details"
→ search_commands_tool("test servers") → Find "list-test-servers" → execute_command_tool("telcocli --profile 5g-val list-test-servers --status-filter online --output table")

User: "list outposts in my-profile profile"
→ search_commands_tool("outposts") → Find "list-outposts" → execute_command_tool("telcocli --profile my-profile list-outposts --output table")

User: "show S3 buckets"
→ search_commands_tool("s3 buckets") → No TelcoCLI command → enhanced_execute_bash_tool("aws s3 ls")

🚨 CRITICAL: Always search the TelcoCLI knowledge base BEFORE using AWS CLI commands. TelcoCLI has 21 specialized commands that should be preferred over direct AWS API calls."""


class TelcoCLIAgent:
    """TelcoCLI AI Agent powered by Strands."""

    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        model: Optional[BedrockModel] = None,
        verbose: bool = False,
    ):
        """Initialize the TelcoCLI agent.

        Args:
            session_manager: Session manager for conversation persistence.
            model: Bedrock model to use. If None, uses default Claude 4.
            verbose: Enable verbose logging.
        """
        import logging

        self.session_manager = session_manager or SessionManager()

        # Validate AWS configuration before initializing model
        try:
            from .credential_cache import validate_credentials_cached

            is_valid, error_msg = validate_credentials_cached()
            if not is_valid and error_msg:
                logger.warning(f"AWS configuration issue: {error_msg}")
        except ImportError:
            # Fallback to original validator if available
            try:
                from telco_cli.utils.aws_config_validator import AWSConfigValidator

                validator = AWSConfigValidator()
                validation_result: Tuple[bool, Optional[str]] = validator.validate()
                is_valid, error_msg_optional = validation_result
                error_msg = error_msg_optional or ""
                if not is_valid and error_msg:
                    logger.warning(f"AWS configuration issue: {error_msg}")
            except ImportError:
                logger.debug("AWS config validator not available")

        # Suppress botocore logging during model initialization unless verbose
        boto_logger = logging.getLogger("botocore")
        original_level = boto_logger.level
        if not verbose:
            boto_logger.setLevel(logging.ERROR)

        try:
            # Use provided model or default to Claude 4 on Bedrock
            if model is None:
                from .config import DEFAULT_MODEL_ID, get_aws_region

                region = get_aws_region()
                logger.info(f"Initializing Bedrock model in region: {region}")

                # Try to create model, fallback to us-east-1 if region doesn't support Bedrock
                try:
                    model = BedrockModel(model_id=DEFAULT_MODEL_ID, region_name=region)
                except Exception as e:
                    error_msg = str(e)
                    if "us-west-2" not in region and (
                        "InvalidRegion" in error_msg or "not supported" in error_msg
                    ):
                        logger.warning(
                            f"Bedrock not available in {region}, trying us-east-1: {error_msg}"
                        )
                        try:
                            model = BedrockModel(model_id=DEFAULT_MODEL_ID, region_name="us-east-1")
                        except Exception as fallback_error:
                            logger.error(
                                f"Failed to initialize Bedrock in fallback region: {fallback_error}"
                            )
                            raise RuntimeError(
                                f"Bedrock initialization failed in both {region} and us-east-1"
                            ) from fallback_error
                    else:
                        logger.error(f"Bedrock initialization failed: {error_msg}")
                        raise

            # Create agent with enhanced MCP tools and system prompt
            try:
                tools = get_enhanced_tools()
                logger.info("Using enhanced MCP-integrated tools")
            except ImportError:
                tools = get_all_tools()
                logger.info("Using standard tools (MCP integration unavailable)")

            self.agent = Agent(
                model=model,
                tools=tools,
                system_prompt=TELCOCLI_SYSTEM_PROMPT,
                callback_handler=None if not verbose else None,  # Use default if verbose
            )
        finally:
            # Restore original logging level
            boto_logger.setLevel(original_level)

        self.verbose = verbose

    def ask(self, query: str, session_id: Optional[str] = None) -> str:
        """Ask the agent a question.

        Args:
            query: User's question or request.
            session_id: Optional session ID to continue a conversation.

        Returns:
            Agent's response.
        """
        # Load or create session
        if session_id:
            if not self.session_manager.load_session(session_id):
                print(f"Warning: Could not load session {session_id}. Creating new session.")
                session_id = self.session_manager.create_session()
        else:
            session_id = self.session_manager.create_session()

        # Add user message to session
        self.session_manager.add_message("user", query)

        # Invoke agent
        try:
            result = self.agent(query)

            # Extract response text
            response = result.message if hasattr(result, "message") else str(result)

            # Track tool uses if available
            tool_uses = []
            if hasattr(result, "metrics") and hasattr(result.metrics, "tool_usage"):
                for tool_name, tool_data in result.metrics.tool_usage.items():
                    tool_uses.append(
                        {
                            "tool": tool_name,
                            "calls": tool_data.get("execution_stats", {}).get("call_count", 0),
                        }
                    )

            # Add assistant response to session
            self.session_manager.add_message(
                "assistant", response, tool_uses if tool_uses else None
            )

            # Print session info if verbose
            if self.verbose:
                session_info = self.session_manager.get_session_info()
                print(f"\n[Session: {session_info['session_id']}]")
                print(
                    f"[Messages: {session_info['total_messages']} | Tools used: {session_info['total_tool_uses']}]"
                )

            return response

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"Agent execution failed: {str(e)}", exc_info=True)

            # Add error to session for context
            if hasattr(self, "session_manager") and self.session_manager:
                self.session_manager.add_message("assistant", error_msg)

            # Re-raise credential errors for proper handling by CLI
            if self._is_credential_error(str(e)):
                raise

            return error_msg
        finally:
            # Ensure session is saved on completion
            if hasattr(self, "session_manager") and self.session_manager:
                self.session_manager.force_save()

    def _is_credential_error(self, error_msg: str) -> bool:
        """Check if error is related to expired/invalid credentials."""
        from .config import is_credential_error

        return is_credential_error(error_msg)

    def get_session_id(self) -> Optional[str]:
        """Get the current session ID.

        Returns:
            Current session ID or None.
        """
        return self.session_manager.current_session_id

    def list_sessions(self, limit: int = 10):
        """List recent sessions.

        Args:
            limit: Maximum number of sessions to return.

        Returns:
            List of session info dictionaries.
        """
        return self.session_manager.list_sessions(limit)


def create_agent(verbose: bool = False) -> TelcoCLIAgent:
    """Create a TelcoCLI agent instance.

    Args:
        verbose: Enable verbose logging.

    Returns:
        Configured TelcoCLIAgent instance.
    """
    return TelcoCLIAgent(verbose=verbose)


# Example usage
if __name__ == "__main__":
    # Create agent
    agent = create_agent(verbose=True)

    # Ask a question
    response = agent.ask("What commands are available for managing VPN certificates?")
    print(response)

    # Get session ID for future reference
    session_id = agent.get_session_id()
    print(f"\nSession ID: {session_id}")

    # Continue conversation in same session
    response = agent.ask("How do I create a new VPN certificate?", session_id=session_id)
    print(response)
