# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Knowledge base builder using existing documentation file."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class DocumentationKnowledgeBaseBuilder:
    """Builds knowledge base from existing documentation file."""

    def __init__(self, doc_path: Optional[Path] = None):
        """Initialize the builder.

        Args:
            doc_path: Path to documentation file. If None, uses default path.
        """
        if doc_path is None:
            # Use the workflow documentation from the current workspace
            current_file = Path(__file__).resolve()
            telcocli_root = current_file.parent.parent.parent.parent.parent
            doc_path = telcocli_root / "doc" / "telcocli-workflows.md"

        self.doc_path = Path(doc_path)
        self.knowledge_base: Dict[str, Any] = {}

    def build(self) -> Dict[str, Any]:
        """Build the knowledge base from documentation.

        Returns:
            Dictionary containing all command documentation.
        """
        self.knowledge_base = {
            "commands": {},
            "categories": {},
            "workflows": {},
            "metadata": {"version": "2.0", "source": "telcocli-workflows.md", "total_commands": 0},
        }

        # Read documentation file
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the documentation
        self._parse_documentation(content)

        self.knowledge_base["metadata"]["total_commands"] = len(self.knowledge_base["commands"])

        return self.knowledge_base

    def _parse_documentation(self, content: str) -> None:
        """Parse the markdown documentation content."""

        # Split content into sections
        sections = re.split(r"^## (\d+\. .+?)$", content, flags=re.MULTILINE)

        # Process each numbered section (categories)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                category_title = sections[i]
                category_content = sections[i + 1]

                # Extract category info
                category_name = self._extract_category_name(category_title)

                # Parse workflows
                workflows = self._extract_workflows(category_content)
                if workflows:
                    self.knowledge_base["workflows"][category_name] = workflows

                # Parse commands in this category
                commands = self._extract_commands(category_content, category_name)

                # Add commands to knowledge base
                for cmd_name, cmd_info in commands.items():
                    self.knowledge_base["commands"][cmd_name] = cmd_info

                    # Add to category
                    if category_name not in self.knowledge_base["categories"]:
                        self.knowledge_base["categories"][category_name] = []
                    self.knowledge_base["categories"][category_name].append(cmd_name)

    def _extract_category_name(self, title: str) -> str:
        """Extract clean category name from title."""
        # Remove number prefix and clean up
        name = re.sub(r"^\d+\.\s*", "", title)
        return name.lower().replace(" ", "-").replace("/", "-")

    def _extract_workflows(self, content: str) -> List[str]:
        """Extract workflow descriptions from category content."""
        workflows = []

        # Look for "Workflows Enabled:" section
        workflow_match = re.search(
            r"\*\*Workflows Enabled:\*\*\s*\n(.*?)(?=\n###|\n---|\Z)", content, re.DOTALL
        )

        if workflow_match:
            workflow_text = workflow_match.group(1)
            # Extract bullet points
            workflow_items = re.findall(r"- \*\*([^*]+)\*\* - ([^\n]+)", workflow_text)
            for name, description in workflow_items:
                workflows.append(f"{name}: {description}")

        return workflows

    def _extract_commands(self, content: str, category: str) -> Dict[str, Dict[str, Any]]:
        """Extract command information from category content."""
        commands = {}

        # Find all command sections (### `command-name`)
        command_sections = re.findall(
            r"### `([^`]+)`\s*\n\*\*Purpose\*\*: ([^\n]+)\s*\n\*\*Usage:\*\*\s*\n```bash\n([^`]+)```\s*\n\*\*Options:\*\*(.*?)\*\*Examples:\*\*(.*?)(?=\n---|### |## |\Z)",
            content,
            re.DOTALL,
        )

        for cmd_name, purpose, usage, options_text, examples_text in command_sections:
            # Parse options
            options = self._parse_options(options_text)

            # Parse examples
            examples = self._parse_examples(examples_text)

            commands[cmd_name] = {
                "name": cmd_name,
                "description": purpose.strip(),
                "usage": usage.strip(),
                "category": category,
                "parameters": options,
                "examples": examples,
                "workflows": self.knowledge_base.get("workflows", {}).get(category, []),
            }

        return commands

    def _parse_options(self, options_text: str) -> List[Dict[str, Any]]:
        """Parse command options from text."""
        options = []

        # Find option lines
        option_lines = re.findall(r"- `([^`]+)` - ([^\n]+)", options_text)

        for option_name, description in option_lines:
            # Check if required
            required = "(required)" in description
            description = re.sub(r"\s*\(required\)", "", description)

            # Extract choices if present
            choices = []
            choices_match = re.search(r"Choices: `([^`]+)`", description)
            if choices_match:
                choices = [c.strip() for c in choices_match.group(1).split(",")]
                description = re.sub(r"\s*- Choices: `[^`]+`", "", description)

            options.append(
                {
                    "name": option_name,
                    "description": description.strip(),
                    "required": required,
                    "choices": choices,
                }
            )

        return options

    def _parse_examples(self, examples_text: str) -> List[Dict[str, str]]:
        """Parse command examples from text."""
        examples = []

        # Find code blocks with comments
        example_blocks = re.findall(r"```bash\n(.*?)```", examples_text, re.DOTALL)

        for block in example_blocks:
            lines = block.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract comment if present
                    comment = ""
                    if "#" in line:
                        parts = line.split("#", 1)
                        if len(parts) == 2:
                            line = parts[0].strip()
                            comment = parts[1].strip()

                    examples.append({"command": line, "description": comment})

        return examples

    def save(self, output_path: Optional[Path] = None) -> None:
        """Save knowledge base to JSON file.

        Args:
            output_path: Path to save JSON file. If None, saves to default location.
        """
        if output_path is None:
            output_path = Path(__file__).parent / "commands.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, indent=2)

        print(f"Knowledge base saved to {output_path}")
        print(f"Total commands: {self.knowledge_base['metadata']['total_commands']}")
        print(f"Categories: {list(self.knowledge_base['categories'].keys())}")


def main():
    """Build and save the knowledge base from documentation."""
    builder = DocumentationKnowledgeBaseBuilder()
    builder.build()
    builder.save()

    # Also create AWS errors knowledge base (same as before)
    aws_errors = {
        "AccessDenied": {
            "description": "IAM permissions issue - the credentials don't have required permissions",
            "common_causes": [
                "Missing IAM policy permissions",
                "Incorrect AWS profile selected",
                "Session token expired",
                "Resource-based policy blocking access",
            ],
            "solutions": [
                "Check IAM policies attached to your user/role",
                "Verify you're using the correct AWS profile with --profile",
                "Refresh your AWS credentials if using temporary credentials",
                "Check resource-based policies (e.g., S3 bucket policies)",
            ],
            "aws_docs": "https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html",
        },
        "InvalidParameterValue": {
            "description": "One or more parameters have invalid values",
            "common_causes": [
                "Incorrect parameter format",
                "Value out of acceptable range",
                "Incompatible parameter combination",
            ],
            "solutions": [
                "Check parameter format in command documentation",
                "Verify parameter values are within acceptable ranges",
                "Review parameter combinations for compatibility",
            ],
            "aws_docs": "https://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html",
        },
        "ResourceNotFound": {
            "description": "The specified resource doesn't exist",
            "common_causes": [
                "Resource ID is incorrect",
                "Resource was deleted",
                "Wrong region selected",
                "Resource in different account",
            ],
            "solutions": [
                "Verify the resource ID is correct",
                "Check if resource exists in the AWS Console",
                "Ensure you're in the correct region with --region",
                "Confirm you're using the correct AWS account",
            ],
            "aws_docs": "https://docs.aws.amazon.com/AWSEC2/latest/APIReference/errors-overview.html",
        },
        "ThrottlingException": {
            "description": "API rate limit exceeded",
            "common_causes": ["Too many API calls in short time", "Shared account limits reached"],
            "solutions": [
                "Implement exponential backoff and retry",
                "Reduce frequency of API calls",
                "Request service quota increase if needed",
            ],
            "aws_docs": "https://docs.aws.amazon.com/general/latest/gr/api-retries.html",
        },
    }

    errors_path = Path(__file__).parent / "aws_errors.json"
    with open(errors_path, "w", encoding="utf-8") as f:
        json.dump(aws_errors, f, indent=2)

    print(f"AWS errors knowledge base saved to {errors_path}")


if __name__ == "__main__":
    main()
