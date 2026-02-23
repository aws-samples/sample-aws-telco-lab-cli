# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Build cached Python module from JSON knowledge base."""

import json
from pathlib import Path


def build_cache():
    """Build commands_cache.py from commands.json and aws_errors.json."""
    kb_dir = Path(__file__).parent

    # Load JSON files
    commands_file = kb_dir / "commands.json"
    errors_file = kb_dir / "aws_errors.json"

    commands = {}
    aws_errors = {}

    if commands_file.exists():
        with open(commands_file, "r") as f:
            commands = json.load(f)

    if errors_file.exists():
        with open(errors_file, "r") as f:
            aws_errors = json.load(f)

    # Generate Python module
    cache_file = kb_dir / "commands_cache.py"

    with open(cache_file, "w") as f:
        f.write('"""Pre-compiled knowledge base for faster access."""\n\n')
        f.write("# Auto-generated from commands.json - do not edit manually\n")
        f.write(
            "# Run: python -m telco_cli.telcocli_agent.knowledge_base.cache_builder to regenerate\n\n"
        )

        f.write(f"COMMANDS = {repr(commands)}\n\n")
        f.write(f"AWS_ERRORS = {repr(aws_errors)}\n")

    print(f"✓ Generated {cache_file}")
    print(f"  Commands: {len(commands)}")
    print(f"  AWS Errors: {len(aws_errors)}")


if __name__ == "__main__":
    build_cache()
