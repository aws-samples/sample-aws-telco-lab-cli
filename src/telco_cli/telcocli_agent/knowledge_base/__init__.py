# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Knowledge base module for TelcoCLI agent."""

from .builder import KnowledgeBaseBuilder
from .loader import load_knowledge_base

__all__ = ["KnowledgeBaseBuilder", "load_knowledge_base"]
