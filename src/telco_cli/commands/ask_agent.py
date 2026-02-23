# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Ask command - Query the TelcoCLI AI agent."""

import argparse
import sys

from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, console_error, get_logger

logger = get_logger(__name__)

__version__ = "1.0.0"


class AskAgentCommand(BaseCommand):
    """Command to ask the TelcoCLI AI agent questions."""

    @property
    def name(self) -> str:
        """Return the command name."""
        return "ask"

    @property
    def description(self) -> str:
        """Return the command description."""
        return "Ask the TelcoCLI AI agent for help and guidance (supports interactive mode)"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments.

        Args:
            parser: Argument parser to register with.
        """
        parser.add_argument(
            "query",
            type=str,
            nargs="?",
            help="Question or request for the AI agent (optional in interactive mode)",
        )
        parser.add_argument(
            "--session", type=str, help="Session ID to continue a previous conversation"
        )
        parser.add_argument(
            "--list-sessions", action="store_true", help="List recent conversation sessions"
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed session information"
        )
        parser.add_argument(
            "--build-kb", action="store_true", help="Rebuild the knowledge base before querying"
        )
        parser.add_argument(
            "--interactive",
            "-i",
            action="store_true",
            help="Start interactive session that continues until exit",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the ask command.

        Args:
            args: Parsed command arguments.
        """
        try:
            # Check if agent dependencies are installed
            try:
                from telco_cli.telcocli_agent import create_agent
                from telco_cli.telcocli_agent.knowledge_base.builder import KnowledgeBaseBuilder
            except ImportError as e:
                console_error.print(
                    "[red]Error: TelcoCLI AI agent dependencies not installed.[/red]\n"
                    f"Details: {str(e)}\n"
                    "Please install with: pip install -r telcocli_agent/requirements.txt"
                )
                sys.exit(1)

            # Check AWS credentials before proceeding
            if not self._check_aws_credentials():
                return

            # Build knowledge base if requested
            if args.build_kb:
                console.print("[yellow]Building knowledge base...[/yellow]")
                builder = KnowledgeBaseBuilder()
                builder.build()
                builder.save()
                console.print("[green]✓ Knowledge base built successfully[/green]\n")

            # Create agent with credential validation and suppressed AWS logging
            import logging

            boto_logger = logging.getLogger("botocore")
            original_level = boto_logger.level

            try:
                # Suppress botocore tracebacks during agent creation
                boto_logger.setLevel(logging.ERROR)
                agent = create_agent(verbose=args.verbose)
            except Exception as e:
                if self._is_credential_error(str(e)):
                    self._handle_credential_error(str(e))
                    return
                raise
            finally:
                # Restore original logging level
                boto_logger.setLevel(original_level)

            # List sessions if requested
            if args.list_sessions:
                self._list_sessions(agent)
                return

            # Start interactive mode or single query
            if args.interactive or not args.query:
                self._run_interactive_session(agent, args)
            else:
                self._run_single_query(agent, args)

        except KeyboardInterrupt:
            console_error.print("\n[yellow]Cancelled by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            if self._is_credential_error(str(e)):
                # Credential errors are already handled in _run_single_query or _run_interactive_session
                pass
            else:
                logger.exception("Error in ask command")
                console_error.print(f"[red]Error: {str(e)}[/red]")
            sys.exit(1)

    def _list_sessions(self, agent) -> None:
        """List recent sessions."""
        sessions = agent.list_sessions(limit=10)
        if not sessions:
            console.print("[yellow]No previous sessions found.[/yellow]")
            return

        console.print("\n[bold]Recent Sessions:[/bold]")
        for i, session in enumerate(sessions, 1):
            console.print(
                f"{i}. Session ID: {session['session_id']}\n"
                f"   Created: {session['created_at']}\n"
                f"   Updated: {session['updated_at']}\n"
                f"   Messages: {session['total_messages']}\n"
            )

    def _run_single_query(self, agent, args) -> None:
        """Run a single query and exit."""
        console.print(f"\n[bold cyan]Question:[/bold cyan] {args.query}\n")
        try:
            response = agent.ask(args.query, session_id=args.session)
            response_text = self._extract_response_text(response)
            console.print(f"[bold green]Agent:[/bold green]\n{response_text}\n")
            self._show_session_info(agent, args.verbose)
        except Exception as e:
            if self._is_credential_error(str(e)):
                self._handle_credential_error(str(e))
                sys.exit(1)
            else:
                console_error.print(f"[red]Error:[/red] {str(e)}\n")
                raise

    def _run_interactive_session(self, agent, args) -> None:
        """Run interactive session until user exits."""
        console.print("\n[bold cyan]🤖 TelcoCLI Interactive Agent[/bold cyan]")
        console.print(
            "[dim]Type your questions or commands. Use /exit to quit, /help for commands.[/dim]\n"
        )

        session_id = args.session

        # Handle initial query if provided
        if args.query:
            console.print(f"[bold cyan]You:[/bold cyan] {args.query}")
            response = agent.ask(args.query, session_id=session_id)
            response_text = self._extract_response_text(response)
            console.print(f"[bold green]Agent:[/bold green] {response_text}\n")
            session_id = agent.get_session_id()

        while True:
            try:
                query = console.input("[bold cyan]You:[/bold cyan] ").strip()

                if not query:
                    continue

                # Handle special commands
                if query.startswith("/"):
                    if self._handle_special_command(query, agent, args):
                        break
                    continue

                # Check for exit commands before processing
                if query.lower() in [
                    "exit",
                    "quit",
                    "bye",
                    "goodbye",
                    "done",
                    "im done",
                    "i'm done",
                ]:
                    console.print("[dim]Goodbye! Session ended.[/dim]")
                    break

                # Ask the agent
                try:
                    response = agent.ask(query, session_id=session_id)
                    response_text = self._extract_response_text(response)
                    console.print(f"[bold green]Agent:[/bold green] {response_text}\n")
                    session_id = agent.get_session_id()
                except Exception as e:
                    if self._is_credential_error(str(e)):
                        console_error.print(f"[red]Credential Error:[/red] {str(e)}\n")
                        if self._offer_credential_refresh():
                            # Retry the same query after credential refresh
                            continue
                        else:
                            break
                    else:
                        console_error.print(f"[red]Error:[/red] {str(e)}\n")
                        console.print("[dim]You can continue with other questions or /exit[/dim]\n")

            except KeyboardInterrupt:
                console.print("\n[yellow]Use /exit to quit properly[/yellow]")
            except EOFError:
                break

        console.print("[dim]Session ended. Goodbye![/dim]")

    def _handle_special_command(self, command: str, agent, args) -> bool:
        """Handle special commands in interactive mode.

        Returns:
            True if should exit, False to continue.
        """
        cmd = command.lower().strip()

        if cmd in ["/exit", "/quit", "/q"]:
            return True

        elif cmd in ["/help", "/h"]:
            console.print("\n[bold]Available Commands:[/bold]")
            console.print("  /exit, /quit, /q  - Exit interactive session")
            console.print("  /help, /h         - Show this help")
            console.print("  /session          - Show current session info")
            console.print("  /sessions         - List recent sessions")
            console.print("  /verbose          - Toggle verbose mode")
            console.print("  /clear            - Clear screen")
            console.print("  /credentials      - Show credential help")
            console.print("  /refresh          - Run credential refresh script")
            console.print("  /clear-cache      - Clear credential validation cache")
            console.print("\n[dim]Or just type your question naturally![/dim]\n")

        elif cmd == "/session":
            self._show_session_info(agent, True)

        elif cmd == "/sessions":
            self._list_sessions(agent)

        elif cmd == "/verbose":
            args.verbose = not args.verbose
            console.print(f"[yellow]Verbose mode: {'ON' if args.verbose else 'OFF'}[/yellow]\n")

        elif cmd == "/clear":
            console.clear()
            console.print("[bold cyan]🤖 TelcoCLI Interactive Agent[/bold cyan]")
            console.print("[dim]Session cleared. Continue asking questions...[/dim]\n")

        elif cmd == "/credentials":
            self._show_credential_help()

        elif cmd == "/refresh":
            console.print("\n[bold cyan]Credential Refresh[/bold cyan]")
            console.print("Please use one of these standard AWS credential refresh methods:\n")
            console.print("[bold]AWS SSO (Recommended):[/bold]")
            console.print("  [cyan]aws sso login --profile <profile-name>[/cyan]\n")
            console.print("[bold]Credential Management Tools:[/bold]")
            console.print(
                "  • aws-vault: [cyan]aws-vault exec <profile> -- telcocli ask ...[/cyan]"
            )
            console.print("  • granted: [cyan]assume <profile>[/cyan]")
            console.print("  • leapp: Use GUI to refresh credentials\n")
            console.print("[bold]Manual Configuration:[/bold]")
            console.print("  [cyan]aws configure --profile <profile-name>[/cyan]\n")

        elif cmd == "/clear-cache":
            from telco_cli.telcocli_agent.credential_cache import (
                clear_credential_cache,
                get_cache_stats,
            )

            stats_before = get_cache_stats()
            clear_credential_cache()
            console.print("[green]✓ Credential cache cleared[/green]")
            console.print(f"[dim]Cleared {stats_before['total_entries']} cached entries[/dim]\n")

        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("[dim]Type /help for available commands[/dim]\n")

        return False

    def _extract_response_text(self, response) -> str:
        """Extract text from agent response."""
        if isinstance(response, dict):
            if "content" in response:
                content = response["content"]
                if isinstance(content, list) and len(content) > 0:
                    return content[0].get("text", str(response))
                else:
                    return str(content)
            else:
                return str(response)
        else:
            return str(response)

    def _show_session_info(self, agent, verbose: bool) -> None:
        """Show session information."""
        session_id = agent.get_session_id()
        if verbose:
            session_info = agent.session_manager.get_session_info()
            console.print(
                f"[dim]Session: {session_id}\n"
                f"Messages: {session_info['total_messages']} | "
                f"Tools used: {session_info['total_tool_uses']}[/dim]\n"
            )
        else:
            console.print(f"[dim]Session ID: {session_id}[/dim]")
            console.print(f"[dim]Use --session {session_id} to continue this conversation[/dim]\n")

    def _is_credential_error(self, error_msg: str) -> bool:
        """Check if error is related to expired/invalid credentials."""
        credential_indicators = [
            "ExpiredToken",
            "ExpiredTokenException",
            "security token included in the request is expired",
            "InvalidUserID.NotFound",
            "SignatureDoesNotMatch",
            "InvalidAccessKeyId",
            "TokenRefreshRequired",
            "CredentialsNotFound",
            "UnauthorizedOperation",
        ]
        return any(indicator in error_msg for indicator in credential_indicators)

    def _handle_credential_error(self, error_msg: str) -> None:
        """Handle credential-related errors with helpful guidance."""
        console_error.print(f"[red]Credential Error:[/red] {error_msg}\n")

        console.print("[bold yellow]⚠️  AWS Credentials Issue Detected[/bold yellow]")

        # Check if user specified a profile
        import os

        current_profile = os.environ.get("AWS_PROFILE", "default")
        console.print(f"\n[bold cyan]Current profile:[/bold cyan] {current_profile}")

        # Show valid profiles from credential check
        valid_profiles = self._get_valid_profiles()
        if valid_profiles:
            console.print(
                f"[bold green]Valid profiles available:[/bold green] {', '.join(valid_profiles)}"
            )
            console.print(
                f"[bold yellow]Suggestion:[/bold yellow] Try: [cyan]telcocli --profile {valid_profiles[0]} ask ...[/cyan]"
            )

        console.print("\n[bold cyan]The 'ask' command requires:[/bold cyan]")
        console.print("  • Valid AWS credentials for the specified profile")
        console.print("  • Bedrock API access permissions in the target region")
        console.print("  • Non-expired session tokens\n")

        self._offer_credential_refresh()

    def _offer_credential_refresh(self) -> bool:
        """Offer credential refresh options to user.

        Returns:
            True if user wants to retry, False to exit.
        """
        console.print("[bold]Credential Refresh Options:[/bold]")
        console.print(
            "  1. Use TelcoCLI credential update: [cyan]telcocli update-credentials <account-id>[/cyan]"
        )
        console.print(
            "  2. Refresh AWS CLI profile: [cyan]aws configure --profile <profile-name>[/cyan]"
        )
        console.print(
            "  3. Set environment variables: [cyan]export AWS_PROFILE=<valid-profile>[/cyan]"
        )
        console.print(
            "  4. Use different profile: [cyan]telcocli --profile <profile> ask ...[/cyan]\n"
        )

        console.print("[bold]Credential Refresh Options:[/bold]")
        console.print("  [cyan]Option A - AWS SSO (Recommended):[/cyan]")
        console.print("    1. Configure SSO: [cyan]aws configure sso[/cyan]")
        console.print("    2. Login: [cyan]aws sso login --profile <profile-name>[/cyan]")
        console.print("  [cyan]Option B - Manual Profile Configuration:[/cyan]")
        console.print(
            "    1. Configure profile: [cyan]aws configure --profile <profile-name>[/cyan]"
        )
        console.print("    2. Set credentials manually or use IAM Identity Center")
        console.print("  [cyan]Option C - Credential Management Tools:[/cyan]")
        console.print("    • aws-vault: [cyan]aws-vault exec <profile> -- telcocli ask ...[/cyan]")
        console.print("    • granted: [cyan]assume <profile>[/cyan]")
        console.print("    • leapp: GUI-based credential management")

        # Show current profile info
        import os

        current_profile = os.environ.get("AWS_PROFILE", "default")
        console.print(
            f"\n[bold yellow]Note:[/bold yellow] You're using profile '[cyan]{current_profile}[/cyan]'"
        )
        console.print("To refresh this profile, use one of the options above.")

        # Show valid profiles as alternatives
        valid_profiles = self._get_valid_profiles()
        if valid_profiles and current_profile not in valid_profiles:
            console.print("\n[bold green]Alternative:[/bold green] Use a valid profile instead:")
            console.print(f"  [cyan]telcocli --profile {valid_profiles[0]} ask ...[/cyan]\n")
        else:
            console.print()

        return False  # Don't attempt automatic refresh
        retry_response = console.input("[bold]Try again with current credentials? (y/N): [/bold]")
        return retry_response.lower() in ["y", "yes"]

    def _show_credential_help(self) -> None:
        """Show credential management help."""
        console.print("\n[bold cyan]🔑 AWS Credentials for TelcoCLI Ask Command[/bold cyan]")
        console.print("\n[bold yellow]Requirements:[/bold yellow]")
        console.print("  • Valid AWS credentials (non-expired session tokens)")
        console.print("  • Bedrock API access in the target region (default: us-west-2)")
        console.print("  • Proper IAM permissions for Bedrock model access\n")

        console.print("[bold]Credential Management Options:[/bold]")
        console.print("  [cyan]AWS SSO (Recommended):[/cyan]")
        console.print("    aws configure sso")
        console.print("    aws sso login --profile <profile-name>")
        console.print("  [cyan]AWS CLI Profiles:[/cyan]")
        console.print("    aws configure --profile <profile-name>")
        console.print("  [cyan]Environment Variables:[/cyan]")
        console.print("    export AWS_PROFILE=<profile-name>")
        console.print("  [cyan]Credential Management Tools:[/cyan]")
        console.print("    • aws-vault: Secure credential storage")
        console.print("    • granted: Fast profile switching")
        console.print("    • leapp: GUI-based management\n")

        console.print("[bold]Usage Examples:[/bold]")
        console.print("  [cyan]telcocli --profile my-bedrock-profile ask 'help me'[/cyan]")
        console.print("  [cyan]AWS_PROFILE=my-profile telcocli ask --interactive[/cyan]")
        console.print("  [cyan]aws-vault exec my-profile -- telcocli ask 'help me'[/cyan]\n")

        console.print("[bold]Troubleshooting:[/bold]")
        console.print("  • ExpiredToken: Refresh credentials using your credential tool")
        console.print("  • UnauthorizedOperation: Check Bedrock permissions")
        console.print("  • Region issues: Ensure Bedrock is available in your region\n")

    def _check_aws_credentials(self) -> bool:
        """Check AWS credentials and guide user through setup if needed.

        Returns:
            True if credentials are valid, False if user needs to configure them.
        """
        import configparser
        import logging
        from pathlib import Path

        from telco_cli.telcocli_agent.credential_cache import get_valid_profiles_cached

        # Temporarily suppress boto3/botocore warnings during credential check
        boto_logger = logging.getLogger("botocore")
        original_level = boto_logger.level
        boto_logger.setLevel(logging.ERROR)

        try:
            credentials_file = Path.home() / ".aws" / "credentials"
            if not credentials_file.exists():
                console_error.print("[yellow]⚠️  No AWS credentials file found[/yellow]")
                return self._guide_credential_setup()

            config = configparser.ConfigParser()
            try:
                config.read(credentials_file)
            except Exception:
                console_error.print("[yellow]⚠️  AWS credentials file is malformed[/yellow]")
                return self._guide_credential_setup()

            if not config.sections():
                console_error.print("[yellow]⚠️  No AWS profiles configured[/yellow]")
                return self._guide_credential_setup()

            # Use cached validation
            valid_profiles = get_valid_profiles_cached()
            invalid_count = len(config.sections()) - len(valid_profiles)

            if valid_profiles:
                console.print(f"[green]✓ Valid AWS profiles: {', '.join(valid_profiles)}[/green]")
                if invalid_count > 0:
                    console_error.print(f"[yellow]⚠️  Invalid profiles: {invalid_count}[/yellow]")
                return True
            else:
                console_error.print("[red]✗ No valid AWS credentials found[/red]")
                return self._guide_credential_refresh()
        finally:
            # Restore original logging level
            boto_logger.setLevel(original_level)

    def _guide_credential_setup(self) -> bool:
        """Guide user through initial AWS credential setup.

        Returns:
            True if user wants to continue, False to exit.
        """
        console.print("\n[bold cyan]AWS Credentials Setup Required[/bold cyan]")
        console.print(
            "\nTelcoCLI requires AWS credentials to function. You have several options:\n"
        )

        console.print("[bold]1. Configure AWS CLI profiles for each account:[/bold]")
        console.print("   [dim]# Management account[/dim]")
        console.print("   aws configure --profile management-account")
        console.print("   [dim]# Outpost account[/dim]")
        console.print("   aws configure --profile outpost-account-us-west-2")
        console.print("   [dim]# Partner accounts[/dim]")
        console.print("   aws configure --profile partner-account-production\n")

        console.print("[bold]2. Use TelcoCLI credential management:[/bold]")
        console.print(
            "   telcocli configure-credentials add --account-id 123456789012 --profiles production"
        )
        console.print("   telcocli update-credentials\n")

        console.print("[bold]3. Set environment variables:[/bold]")
        console.print("   export AWS_PROFILE=your-profile")
        console.print("   export AWS_DEFAULT_REGION=us-west-2\n")

        console.print(
            "[dim]For detailed setup instructions, see: doc/telcocli-workflows.md[/dim]\n"
        )

        response = console.input("[bold]Continue without credentials? (y/N): [/bold]")
        return response.lower() in ["y", "yes"]

    def _guide_credential_refresh(self) -> bool:
        """Guide user through credential refresh process.

        Returns:
            True if user wants to continue, False to exit.
        """
        console.print("\n[bold cyan]AWS Credentials Expired[/bold cyan]")
        console.print("\nYour AWS credentials have expired. Please refresh them:\n")

        console.print("[bold]Option 1: AWS SSO (Recommended):[/bold]")
        console.print("   aws sso login --profile your-profile-name\n")

        console.print("[bold]Option 2: AWS CLI Profile:[/bold]")
        console.print("   aws configure --profile your-profile-name\n")

        console.print("[bold]Option 3: Credential Management Tools:[/bold]")
        console.print("   • aws-vault: aws-vault exec <profile> -- telcocli ask ...")
        console.print("   • granted: assume <profile>")
        console.print("   • leapp: Use GUI to refresh credentials\n")

        console.print("[bold]Option 4: Environment Variables:[/bold]")
        console.print("   export AWS_PROFILE=refreshed-profile")
        console.print("   export AWS_ACCESS_KEY_ID=your-key")
        console.print("   export AWS_SECRET_ACCESS_KEY=your-secret\n")

        response = console.input("[bold]Continue with expired credentials? (y/N): [/bold]")
        return response.lower() in ["y", "yes"]

    def _get_valid_profiles(self) -> list:
        """Get list of valid AWS profiles with caching.

        Returns:
            List of valid profile names.
        """
        from telco_cli.telcocli_agent.credential_cache import get_valid_profiles_cached

        return get_valid_profiles_cached()
