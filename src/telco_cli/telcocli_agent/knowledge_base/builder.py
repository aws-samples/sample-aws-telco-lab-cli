# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Knowledge base builder - parses TelcoCLI commands to build documentation."""

import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class KnowledgeBaseBuilder:
    """Builds knowledge base by parsing TelcoCLI command files."""

    def __init__(self, commands_dir: Optional[Path] = None):
        """Initialize the builder.

        Args:
            commands_dir: Path to commands directory. If None, auto-detects.
        """
        if commands_dir is None:
            # Auto-detect commands directory
            current_file = Path(__file__).resolve()
            telcocli_root = current_file.parent.parent.parent
            commands_dir = telcocli_root / "src" / "telco_cli" / "commands"

        self.commands_dir = Path(commands_dir)
        self.knowledge_base: Dict[str, Any] = {}

    def build(self) -> Dict[str, Any]:
        """Build the knowledge base by parsing all command files.

        Returns:
            Dictionary containing all command documentation.
        """
        self.knowledge_base = {
            "commands": {},
            "categories": {},
            "metadata": {"version": "1.0", "total_commands": 0},
        }

        # Parse all Python files in commands directory
        for py_file in self.commands_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            # Validate file path to prevent traversal attacks
            if not self._is_safe_path(py_file):
                continue

            command_info = self._parse_command_file(py_file)
            if command_info:
                cmd_name = command_info["name"]
                self.knowledge_base["commands"][cmd_name] = command_info

                # Categorize
                category = command_info.get("category", "general")
                if category not in self.knowledge_base["categories"]:
                    self.knowledge_base["categories"][category] = []
                self.knowledge_base["categories"][category].append(cmd_name)

        self.knowledge_base["metadata"]["total_commands"] = len(self.knowledge_base["commands"])

        return self.knowledge_base

    def _parse_command_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a single command file to extract documentation.

        Args:
            file_path: Path to the command file.

        Returns:
            Dictionary with command information or None if not a command file.
        """
        try:
            # Additional path validation before opening
            if not self._is_safe_path(file_path):
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Find the command class
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name.endswith("Command") and node.name != "BaseCommand":
                        return self._extract_command_info(node, file_path)

            return None

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def _extract_command_info(self, class_node: ast.ClassDef, file_path: Path) -> Dict[str, Any]:
        """Extract command information from AST class node.

        Args:
            class_node: AST node for the command class.
            file_path: Path to the source file.

        Returns:
            Dictionary with command details.
        """
        command_info: Dict[str, Any] = {
            "class_name": class_node.name,
            "name": "",
            "description": "",
            "parameters": [],
            "category": self._get_category_from_path(file_path),
            "file_path": str(file_path.relative_to(self.commands_dir.parent.parent)),
        }

        # Extract docstring
        docstring = ast.get_docstring(class_node)
        if docstring:
            command_info["docstring"] = docstring.strip()

        # Find methods to extract name, description, and parameters
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name == "name":
                    command_info["name"] = self._extract_return_value(item)
                elif item.name == "description":
                    command_info["description"] = self._extract_return_value(item)
                elif item.name == "register" or item.name == "add_arguments":
                    extracted_params = self._extract_parameters(item)
                    command_info["parameters"] = extracted_params

        return command_info

    def _extract_return_value(self, func_node: ast.FunctionDef) -> str:
        """Extract return value from a simple function.

        Args:
            func_node: AST node for the function.

        Returns:
            The return value as a string.
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value:
                if isinstance(node.value, ast.Constant):
                    value = node.value.value
                    return str(value) if isinstance(value, str) else ""
                elif isinstance(node.value, ast.Str):  # Python 3.7 compatibility
                    return str(node.value.s)
        return ""

    def _extract_parameters(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract command parameters from register/add_arguments method.

        Args:
            func_node: AST node for the register function.

        Returns:
            List of parameter dictionaries.
        """
        parameters = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                # Look for parser.add_argument calls
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":

                    param_info = {"name": "", "help": "", "required": False, "type": "str"}

                    # Extract positional argument (parameter name)
                    if node.args:
                        if isinstance(node.args[0], ast.Constant):
                            param_info["name"] = node.args[0].value
                        elif isinstance(node.args[0], ast.Str):
                            param_info["name"] = node.args[0].s

                    # Extract keyword arguments
                    for keyword in node.keywords:
                        if keyword.arg == "help":
                            if isinstance(keyword.value, ast.Constant):
                                param_info["help"] = keyword.value.value
                            elif isinstance(keyword.value, ast.Str):
                                param_info["help"] = keyword.value.s
                        elif keyword.arg == "required":
                            if isinstance(keyword.value, ast.Constant):
                                param_info["required"] = keyword.value.value
                        elif keyword.arg == "type":
                            param_info["type"] = "custom"

                    if param_info["name"]:
                        parameters.append(param_info)

        return parameters

    def _get_category_from_path(self, file_path: Path) -> str:
        """Determine category from file path.

        Args:
            file_path: Path to the command file.

        Returns:
            Category name.
        """
        # Check if in subdirectory (e.g., vpn/)
        relative_path = file_path.relative_to(self.commands_dir)
        if len(relative_path.parts) > 1:
            return relative_path.parts[0]

        # Categorize by name patterns
        name = file_path.stem
        if "partner" in name:
            return "partner-management"
        elif "outpost" in name:
            return "outpost-management"
        elif "dedicated" in name or "host" in name:
            return "dedicated-hosts"
        elif "eks" in name:
            return "eks"
        elif "credential" in name:
            return "credentials"
        elif "ssm" in name:
            return "ssm"
        else:
            return "general"

    def _is_safe_path(self, file_path: Path) -> bool:
        """Validate file path to prevent path traversal attacks.

        Args:
            file_path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve the path to get absolute path
            resolved_path = file_path.resolve()

            # Check if path is within allowed directories
            allowed_dirs = [
                self.commands_dir.resolve(),
                Path(__file__).parent.resolve(),  # Knowledge base directory
            ]

            # Ensure the resolved path is within one of the allowed directories
            for allowed_dir in allowed_dirs:
                try:
                    resolved_path.relative_to(allowed_dir)
                    return True
                except ValueError:
                    continue

            return False

        except (OSError, ValueError):
            return False

    def save(self, output_path: Optional[Path] = None) -> None:
        """Save knowledge base to JSON file.

        Args:
            output_path: Path to save JSON file. If None, saves to default location.
        """
        if output_path is None:
            output_path = Path(__file__).parent / "commands.json"

        # Validate output path to prevent traversal attacks
        if not self._is_safe_path(output_path):
            raise ValueError("Invalid output path: potential path traversal detected")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_base, f, indent=2)

        print(f"Knowledge base saved to {output_path}")
        print(f"Total commands: {self.knowledge_base['metadata']['total_commands']}")


def main():
    """Build and save the knowledge base."""
    builder = KnowledgeBaseBuilder()
    builder.build()
    builder.save()

    # Also create AWS errors knowledge base
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
