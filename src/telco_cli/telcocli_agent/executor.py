# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Command execution with user confirmation."""

import shlex
import subprocess


class CommandExecutor:
    """Handles command execution with user confirmation."""

    def __init__(self):
        self.trusted_tools = set()

    def execute_with_confirmation(self, command: str, purpose: str) -> tuple[bool, str]:
        """Execute command with user confirmation.

        Args:
            command: The command to execute
            purpose: Description of what the command does

        Returns:
            Tuple of (success, output)
        """
        print("\n🛠️  Using tool: execute_bash")
        print(" ⋮ ")
        print(" ● I will run the following shell command: ")
        print(f"{command}")
        print(" ⋮ ")
        print(f" ↳ Purpose: {purpose}")
        print()

        # Check if this tool is trusted for the session
        tool_key = "execute_bash"
        if tool_key in self.trusted_tools:
            print("✓ Tool is trusted for this session, executing automatically...")
            return self._execute_command(command)

        # Ask for confirmation
        while True:
            response = input(
                "Allow this action? Use 't' to trust (always allow) this tool for the session. [y/n/t]: "
            )
            response = response.lower().strip()

            if response == "y":
                return self._execute_command(command)
            elif response == "n":
                return False, "Command execution cancelled by user"
            elif response == "t":
                self.trusted_tools.add(tool_key)
                print("✓ Tool trusted for this session")
                return self._execute_command(command)
            else:
                print("Please enter 'y' (yes), 'n' (no), or 't' (trust)")

    def _execute_command(self, command: str) -> tuple[bool, str]:
        """Execute the command and return results.

        Args:
            command: Command to execute

        Returns:
            Tuple of (success, output)
        """
        try:
            # Validate and sanitize command to prevent injection
            if not self._is_safe_command(command):
                return False, "Command rejected: potentially unsafe command detected"

            # Validate command length to prevent buffer overflow attacks
            if len(command) > 10000:
                return False, "Command rejected: command too long (max 10000 characters)"

            print()
            # SECURITY: Always use shell=False with parsed arguments
            # Never fall back to shell=True as it enables command injection
            try:
                args = shlex.split(command)
            except ValueError as e:
                # Reject malformed commands instead of falling back to shell=True
                return False, f"Command rejected: invalid command format - {e}"

            # Execute with shell=False for security
            result = subprocess.run(args, capture_output=True, text=True, timeout=30, shell=False)

            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += result.stderr

            success = result.returncode == 0

            # Print the output
            if output.strip():
                print(output)

            print(" ⋮ ")
            print(" ● Completed in 0.500s")  # Placeholder timing
            print()

            return success, output

        except subprocess.TimeoutExpired:
            error_msg = "Command timed out after 30 seconds"
            print(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            print(error_msg)
            return False, error_msg

    def _is_safe_command(self, command: str) -> bool:
        """Validate command safety to prevent injection attacks.

        Args:
            command: Command to validate

        Returns:
            True if command is safe, False otherwise
        """
        # List of dangerous patterns to reject
        dangerous_patterns = [
            ";",
            "&&",
            "||",
            "|",
            ">",
            ">>",
            "<",
            "`",
            "$(",
            "rm -rf",
            "sudo",
            "su ",
            "chmod 777",
            "wget",
            "curl",
            "nc ",
            "netcat",
            "/dev/",
            "/proc/",
            "eval",
            "exec",
        ]

        command_lower = command.lower()

        # Check for dangerous patterns
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False

        # Allow only specific safe commands
        safe_commands = [
            "telcocli",
            "aws",
            "echo",
            "ls",
            "cat",
            "grep",
            "head",
            "tail",
            "wc",
            "sort",
            "uniq",
            "find",
            "which",
            "whoami",
            "pwd",
            "date",
        ]

        # Extract the first word (command name)
        first_word = command.strip().split()[0] if command.strip() else ""

        # Check if command starts with a safe command
        return any(first_word.startswith(safe_cmd) for safe_cmd in safe_commands)


# Global executor instance
_executor = CommandExecutor()


def execute_command_with_confirmation(command: str, purpose: str) -> tuple[bool, str]:
    """Execute command with user confirmation.

    Args:
        command: The command to execute
        purpose: Description of what the command does

    Returns:
        Tuple of (success, output)
    """
    return _executor.execute_with_confirmation(command, purpose)
