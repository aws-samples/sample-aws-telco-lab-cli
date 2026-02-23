# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""TelcoCLI AI Agent - Strands-based assistant for TelcoCLI operations."""

from .agent import TelcoCLIAgent, create_agent
from .session_manager import SessionManager
from .tools import get_all_tools

__version__ = "1.0.0"
__all__ = ["TelcoCLIAgent", "create_agent", "SessionManager", "get_all_tools"]
