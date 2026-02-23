"""Tests for Ask Agent Command - Critical Functionality."""

import argparse
from unittest.mock import Mock, patch

import pytest

from telco_cli.commands.ask_agent import AskAgentCommand

# Check if telcocli_agent is available
try:
    import telco_cli.telcocli_agent  # noqa: F401

    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False


class TestAskAgentCommand:
    """Test cases for AskAgentCommand critical functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = AskAgentCommand()
        self.mock_agent = Mock()
        self.mock_agent.ask.return_value = "Agent response"
        self.mock_agent.get_session_id.return_value = "session-123"
        self.mock_agent.list_sessions.return_value = []
        self.mock_agent.session_manager = Mock()
        self.mock_agent.session_manager.get_session_info.return_value = {
            "session_id": "session-123",
            "total_messages": 2,
            "total_tool_uses": 1,
        }

    def teardown_method(self):
        """Clean up after each test."""
        self.mock_agent.reset_mock()
        self.command = None

    # ===== Command Properties =====

    def test_name_property(self):
        """Test command name is 'ask'."""
        assert self.command.name == "ask"

    def test_description_property(self):
        """Test command description contains key terms."""
        assert "AI agent" in self.command.description
        assert "interactive mode" in self.command.description.lower()

    # ===== Argument Registration =====

    def test_register_arguments(self):
        """Test all required arguments are registered."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # Test query argument
        args = parser.parse_args(["test query"])
        assert args.query == "test query"

        # Test optional flags
        args = parser.parse_args(["--list-sessions"])
        assert args.list_sessions is True

        # Test combined arguments
        args = parser.parse_args(["query", "--session", "abc123", "--verbose", "--interactive"])
        assert args.session == "abc123"
        assert args.verbose is True
        assert args.interactive is True

    # ===== Response Text Extraction =====

    def test_extract_response_text_string(self):
        """Test extracting response from plain string."""
        response = "Simple response"
        result = self.command._extract_response_text(response)
        assert result == "Simple response"

    def test_extract_response_text_dict_with_content_list(self):
        """Test extracting response from dict with content list."""
        response = {"content": [{"text": "Response text"}]}
        result = self.command._extract_response_text(response)
        assert result == "Response text"

    def test_extract_response_text_dict_with_string_content(self):
        """Test extracting response from dict with string content."""
        response = {"content": "String content"}
        result = self.command._extract_response_text(response)
        assert result == "String content"

    def test_extract_response_text_dict_without_content(self):
        """Test extracting response from dict without content key."""
        response = {"other_key": "value"}
        result = self.command._extract_response_text(response)
        assert "other_key" in result

    # ===== Credential Error Detection =====

    def test_is_credential_error_expired_token(self):
        """Test detection of expired token error."""
        assert self.command._is_credential_error("ExpiredToken: Token expired") is True

    def test_is_credential_error_invalid_access_key(self):
        """Test detection of invalid access key error."""
        assert self.command._is_credential_error("InvalidAccessKeyId") is True

    def test_is_credential_error_unauthorized(self):
        """Test detection of unauthorized operation error."""
        assert self.command._is_credential_error("UnauthorizedOperation") is True

    def test_is_credential_error_non_credential_error(self):
        """Test non-credential errors are not detected."""
        assert self.command._is_credential_error("ResourceNotFoundException") is False

    # ===== Special Commands in Interactive Mode =====

    def test_handle_special_command_exit(self):
        """Test /exit command returns True to exit."""
        args = Mock()
        assert self.command._handle_special_command("/exit", self.mock_agent, args) is True

    def test_handle_special_command_quit(self):
        """Test /quit command returns True to exit."""
        args = Mock()
        assert self.command._handle_special_command("/quit", self.mock_agent, args) is True

    def test_handle_special_command_help(self):
        """Test /help command displays help and continues."""
        args = Mock()
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            result = self.command._handle_special_command("/help", self.mock_agent, args)

        assert result is False
        mock_console.print.assert_called()

    def test_handle_special_command_verbose_toggle(self):
        """Test /verbose command toggles verbose mode."""
        args = Mock()
        args.verbose = False

        with patch("telco_cli.commands.ask_agent.console"):
            self.command._handle_special_command("/verbose", self.mock_agent, args)

        assert args.verbose is True

    def test_handle_special_command_session(self):
        """Test /session command shows session info."""
        args = Mock()
        with patch.object(self.command, "_show_session_info") as mock_show:
            result = self.command._handle_special_command("/session", self.mock_agent, args)

        assert result is False
        mock_show.assert_called_once_with(self.mock_agent, True)

    def test_handle_special_command_sessions(self):
        """Test /sessions command lists sessions."""
        args = Mock()
        with patch.object(self.command, "_list_sessions") as mock_list:
            result = self.command._handle_special_command("/sessions", self.mock_agent, args)

        assert result is False
        mock_list.assert_called_once_with(self.mock_agent)

    def test_handle_special_command_clear(self):
        """Test /clear command clears screen."""
        args = Mock()
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            result = self.command._handle_special_command("/clear", self.mock_agent, args)

        assert result is False
        mock_console.clear.assert_called_once()

    def test_handle_special_command_unknown(self):
        """Test unknown special command shows error."""
        args = Mock()
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            result = self.command._handle_special_command("/unknown", self.mock_agent, args)

        assert result is False
        mock_console.print.assert_called()

    # ===== Session Info Display =====

    def test_show_session_info_verbose(self):
        """Test session info display in verbose mode."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._show_session_info(self.mock_agent, verbose=True)

        self.mock_agent.session_manager.get_session_info.assert_called_once()
        mock_console.print.assert_called()

    def test_show_session_info_non_verbose(self):
        """Test session info display in non-verbose mode."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._show_session_info(self.mock_agent, verbose=False)

        mock_console.print.assert_called()
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Session ID" in call for call in print_calls)

    # ===== Session Listing =====

    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        self.mock_agent.list_sessions.return_value = []

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._list_sessions(self.mock_agent)

        mock_console.print.assert_called()
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("No previous sessions" in call for call in print_calls)

    def test_list_sessions_with_data(self):
        """Test listing sessions with existing sessions."""
        self.mock_agent.list_sessions.return_value = [
            {
                "session_id": "session-1",
                "created_at": "2025-11-09T10:00:00",
                "updated_at": "2025-11-09T10:30:00",
                "total_messages": 5,
            }
        ]

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._list_sessions(self.mock_agent)

        self.mock_agent.list_sessions.assert_called_once()
        mock_console.print.assert_called()

    # ===== Credential Setup Guides =====

    def test_guide_credential_setup_continue(self):
        """Test credential setup guide with user continuing."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.return_value = "y"
            result = self.command._guide_credential_setup()

        assert result is True

    def test_guide_credential_setup_exit(self):
        """Test credential setup guide with user exiting."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.return_value = "n"
            result = self.command._guide_credential_setup()

        assert result is False

    def test_guide_credential_refresh_continue(self):
        """Test credential refresh guide with user continuing."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.return_value = "y"
            result = self.command._guide_credential_refresh()

        assert result is True

    def test_guide_credential_refresh_exit(self):
        """Test credential refresh guide with user exiting."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.return_value = "n"
            result = self.command._guide_credential_refresh()

        assert result is False

    # ===== Credential Help Display =====

    def test_show_credential_help(self):
        """Test credential help displays information."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._show_credential_help()

        mock_console.print.assert_called()
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Credentials" in call for call in print_calls)

    # ===== Credential Refresh Guidance =====

    def test_refresh_command_shows_guidance(self):
        """Test /refresh command shows credential refresh guidance."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            result = self.command._handle_special_command("/refresh", Mock(), Mock())

        # Should not exit
        assert result is False

        # Should show credential refresh guidance
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Credential Refresh" in call for call in print_calls)
        assert any("aws sso login" in call for call in print_calls)
        assert any("aws-vault" in call for call in print_calls)
        assert any("granted" in call for call in print_calls)

    def test_refresh_command_shows_standard_tools(self):
        """Test /refresh command recommends standard AWS credential tools."""
        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._handle_special_command("/refresh", Mock(), Mock())

        print_calls = [str(call) for call in mock_console.print.call_args_list]
        # Verify it shows AWS SSO (recommended approach)
        assert any("AWS SSO" in call for call in print_calls)
        # Verify it shows credential management tools
        assert any(
            "aws-vault" in call or "granted" in call or "leapp" in call for call in print_calls
        )
        # Verify it shows manual configuration option
        assert any("aws configure" in call for call in print_calls)

    # ===== Edge Cases and Argument Validation =====

    def test_register_arguments_short_form_interactive(self):
        """Test -i short form for --interactive flag."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        args = parser.parse_args(["-i", "test query"])
        assert args.interactive is True
        assert args.query == "test query"

        args = parser.parse_args(["--interactive", "test query"])
        assert args.interactive is True

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_list_sessions_ignores_query(self, mock_create_agent):
        """Test --list-sessions takes precedence over query argument."""
        mock_create_agent.return_value = self.mock_agent
        self.mock_agent.list_sessions.return_value = []

        args = argparse.Namespace(
            query="this should be ignored",
            session=None,
            list_sessions=True,
            verbose=False,
            build_kb=False,
            interactive=False,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=True):
            with patch("telco_cli.commands.ask_agent.console"):
                self.command.run(args)

        self.mock_agent.list_sessions.assert_called_once()
        self.mock_agent.ask.assert_not_called()

    def test_interactive_with_list_sessions_flags(self):
        """Test that both --interactive and --list-sessions can be parsed."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        args = parser.parse_args(["--interactive", "--list-sessions"])
        assert args.interactive is True
        assert args.list_sessions is True

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_interactive_mode_with_empty_query(self, mock_create_agent):
        """Test interactive mode with no initial query."""
        mock_create_agent.return_value = self.mock_agent
        args = argparse.Namespace(
            query=None,
            session=None,
            list_sessions=False,
            verbose=False,
            build_kb=False,
            interactive=True,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=True):
            with patch("telco_cli.commands.ask_agent.console") as mock_console:
                mock_console.input.return_value = "/exit"
                self.command.run(args)

        mock_console.print.assert_called()

    # ===== Knowledge Base Build Tests =====

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_build_kb_flag(self, mock_create_agent):
        """Test --build-kb flag rebuilds knowledge base."""
        mock_create_agent.return_value = self.mock_agent
        args = argparse.Namespace(
            query="test",
            session=None,
            list_sessions=False,
            verbose=False,
            build_kb=True,
            interactive=False,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=True):
            with patch("telco_cli.commands.ask_agent.console"):
                with patch(
                    "telco_cli.telcocli_agent.knowledge_base.builder.KnowledgeBaseBuilder"
                ) as mock_kb:
                    mock_builder = Mock()
                    mock_kb.return_value = mock_builder

                    self.command.run(args)

                    mock_builder.build.assert_called_once()
                    mock_builder.save.assert_called_once()

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_build_kb_with_query(self, mock_create_agent):
        """Test --build-kb flag combined with query execution."""
        mock_create_agent.return_value = self.mock_agent
        args = argparse.Namespace(
            query="test query after kb build",
            session=None,
            list_sessions=False,
            verbose=False,
            build_kb=True,
            interactive=False,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=True):
            with patch("telco_cli.commands.ask_agent.console"):
                with patch(
                    "telco_cli.telcocli_agent.knowledge_base.builder.KnowledgeBaseBuilder"
                ) as mock_kb:
                    mock_builder = Mock()
                    mock_kb.return_value = mock_builder

                    self.command.run(args)

                    mock_builder.build.assert_called_once()
                    mock_builder.save.assert_called_once()
                    self.mock_agent.ask.assert_called_once_with(
                        "test query after kb build", session_id=None
                    )

    # ===== Core Functionality: run() Method Integration Tests =====

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_run_with_single_query(self, mock_create_agent):
        """Test run() method with single query execution path."""
        mock_create_agent.return_value = self.mock_agent
        args = argparse.Namespace(
            query="How do I create a VPN?",
            session=None,
            list_sessions=False,
            verbose=False,
            build_kb=False,
            interactive=False,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=True):
            with patch("telco_cli.commands.ask_agent.console"):
                self.command.run(args)

        self.mock_agent.ask.assert_called_once_with("How do I create a VPN?", session_id=None)

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_run_with_session_continuation(self, mock_create_agent):
        """Test run() method with session continuation."""
        mock_create_agent.return_value = self.mock_agent
        args = argparse.Namespace(
            query="Follow up question",
            session="previous-session-123",
            list_sessions=False,
            verbose=True,
            build_kb=False,
            interactive=False,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=True):
            with patch("telco_cli.commands.ask_agent.console"):
                self.command.run(args)

        self.mock_agent.ask.assert_called_once_with(
            "Follow up question", session_id="previous-session-123"
        )

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_run_interactive_mode_flag(self, mock_create_agent):
        """Test run() method with interactive flag."""
        mock_create_agent.return_value = self.mock_agent
        args = argparse.Namespace(
            query="Initial question",
            session=None,
            list_sessions=False,
            verbose=False,
            build_kb=False,
            interactive=True,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=True):
            with patch("telco_cli.commands.ask_agent.console") as mock_console:
                mock_console.input.return_value = "/exit"
                self.command.run(args)

        self.mock_agent.ask.assert_called()
        mock_console.print.assert_called()

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    @patch("telco_cli.telcocli_agent.create_agent")
    def test_run_with_failed_credentials(self, mock_create_agent):
        """Test run() method when credential check fails."""
        args = argparse.Namespace(
            query="test",
            session=None,
            list_sessions=False,
            verbose=False,
            build_kb=False,
            interactive=False,
        )

        with patch.object(self.command, "_check_aws_credentials", return_value=False):
            self.command.run(args)

        mock_create_agent.assert_not_called()

    # ===== Core Functionality: run single query Tests =====

    def test_run_single_query_success(self):
        """Test _run_single_query executes query and displays response."""
        args = argparse.Namespace(query="Test query", session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._run_single_query(self.mock_agent, args)

        self.mock_agent.ask.assert_called_once_with("Test query", session_id=None)
        assert mock_console.print.call_count >= 2

    def test_run_single_query_with_session(self):
        """Test _run_single_query with existing session."""
        args = argparse.Namespace(query="Follow up", session="session-abc", verbose=True)

        with patch("telco_cli.commands.ask_agent.console"):
            self.command._run_single_query(self.mock_agent, args)

        self.mock_agent.ask.assert_called_once_with("Follow up", session_id="session-abc")

    def test_run_single_query_with_dict_response(self):
        """Test _run_single_query handles dict response correctly."""
        self.mock_agent.ask.return_value = {"content": [{"text": "Dict response"}]}
        args = argparse.Namespace(query="Test", session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._run_single_query(self.mock_agent, args)

        mock_console.print.assert_called()
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Dict response" in call for call in print_calls)

    def test_run_single_query_credential_error(self):
        """Test _run_single_query handles credential errors."""
        self.mock_agent.ask.side_effect = Exception("ExpiredToken: Token has expired")
        args = argparse.Namespace(query="Test", session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            with patch("telco_cli.commands.ask_agent.console_error"):
                with patch.object(self.command, "_get_valid_profiles", return_value=[]):
                    mock_console.input.return_value = "n"
                    with pytest.raises(SystemExit):
                        self.command._run_single_query(self.mock_agent, args)

    def test_run_single_query_non_credential_error(self):
        """Test _run_single_query handles non-credential errors."""
        self.mock_agent.ask.side_effect = Exception("ResourceNotFoundException: Resource not found")
        args = argparse.Namespace(query="Test", session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console"):
            with patch("telco_cli.commands.ask_agent.console_error") as mock_error_console:
                with pytest.raises(Exception) as exc_info:
                    self.command._run_single_query(self.mock_agent, args)

                mock_error_console.print.assert_called()
                assert "ResourceNotFoundException" in str(exc_info.value)

    def test_run_single_query_verbose_mode(self):
        """Test _run_single_query displays session info in verbose mode."""
        args = argparse.Namespace(query="Test", session=None, verbose=True)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            self.command._run_single_query(self.mock_agent, args)

        self.mock_agent.session_manager.get_session_info.assert_called_once()
        mock_console.print.assert_called()

    # ===== Core Functionality: run interactive session Tests =====

    def test_run_interactive_session_with_initial_query(self):
        """Test _run_interactive_session with initial query."""
        args = argparse.Namespace(query="Initial question", session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.return_value = "/exit"
            self.command._run_interactive_session(self.mock_agent, args)

        self.mock_agent.ask.assert_called()
        assert self.mock_agent.ask.call_count >= 1

    def test_run_interactive_session_without_initial_query(self):
        """Test _run_interactive_session starting fresh without query."""
        args = argparse.Namespace(query=None, session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.return_value = "/exit"
            self.command._run_interactive_session(self.mock_agent, args)

        mock_console.print.assert_called()

    def test_run_interactive_session_multiple_queries(self):
        """Test _run_interactive_session handles multiple user queries."""
        args = argparse.Namespace(query=None, session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.side_effect = ["First question", "Second question", "/exit"]
            self.command._run_interactive_session(self.mock_agent, args)

        assert self.mock_agent.ask.call_count == 2

    def test_run_interactive_session_exit_keywords(self):
        """Test _run_interactive_session exits on exit keywords."""
        args = argparse.Namespace(query=None, session=None, verbose=False)

        exit_keywords = ["exit", "quit", "bye", "goodbye"]
        for keyword in exit_keywords:
            self.mock_agent.ask.reset_mock()
            with patch("telco_cli.commands.ask_agent.console") as mock_console:
                mock_console.input.return_value = keyword
                self.command._run_interactive_session(self.mock_agent, args)

            mock_console.print.assert_called()

    def test_run_interactive_session_empty_input(self):
        """Test _run_interactive_session ignores empty input."""
        args = argparse.Namespace(query=None, session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.side_effect = ["", "  ", "/exit"]
            self.command._run_interactive_session(self.mock_agent, args)

        self.mock_agent.ask.assert_not_called()

    def test_run_interactive_session_credential_error_during_query(self):
        """Test _run_interactive_session handles credential errors gracefully."""
        args = argparse.Namespace(query=None, session=None, verbose=False)
        self.mock_agent.ask.side_effect = Exception("ExpiredToken: Token expired")

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            with patch("telco_cli.commands.ask_agent.console_error"):
                mock_console.input.side_effect = ["test query", "/exit"]
                with patch.object(self.command, "_offer_credential_refresh", return_value=False):
                    self.command._run_interactive_session(self.mock_agent, args)

        self.mock_agent.ask.assert_called()

    def test_run_interactive_session_eof_error(self):
        """Test _run_interactive_session handles EOFError (Ctrl+D)."""
        args = argparse.Namespace(query=None, session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.side_effect = EOFError()
            self.command._run_interactive_session(self.mock_agent, args)

        mock_console.print.assert_called()

    def test_run_interactive_session_keyboard_interrupt(self):
        """Test _run_interactive_session handles KeyboardInterrupt (Ctrl+C)."""
        args = argparse.Namespace(query=None, session=None, verbose=False)

        with patch("telco_cli.commands.ask_agent.console") as mock_console:
            mock_console.input.side_effect = [KeyboardInterrupt(), "/exit"]
            self.command._run_interactive_session(self.mock_agent, args)

        mock_console.print.assert_called()

    # ===== Valid Profiles Tests =====

    def test_handle_credential_error_with_valid_profiles(self):
        """Test _handle_credential_error when valid profiles are available."""
        error_msg = "ExpiredToken: Token has expired"

        with patch.object(
            self.command, "_get_valid_profiles", return_value=["profile1", "profile2"]
        ):
            with patch("telco_cli.commands.ask_agent.console") as mock_console:
                with patch("telco_cli.commands.ask_agent.console_error"):
                    mock_console.input.return_value = "n"
                    with patch("os.environ.get", return_value="default"):
                        self.command._handle_credential_error(error_msg)

        print_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("profile1" in call for call in print_calls)
        assert any("profile2" in call for call in print_calls)

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    def test_handle_credential_error_without_valid_profiles(self):
        """Test _handle_credential_error when no valid profiles are available."""
        error_msg = "InvalidAccessKeyId: The security token included in the request is invalid"

        with patch.object(self.command, "_get_valid_profiles", return_value=[]):
            with patch("telco_cli.commands.ask_agent.console") as mock_console:
                with patch("telco_cli.commands.ask_agent.console_error") as mock_error_console:
                    mock_console.input.return_value = "n"
                    with patch("os.environ.get", return_value="default"):
                        self.command._handle_credential_error(error_msg)

        mock_error_console.print.assert_called()

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    def test_get_valid_profiles(self):
        """Test _get_valid_profiles returns cached valid profiles."""
        with patch(
            "telco_cli.telcocli_agent.credential_cache.get_valid_profiles_cached",
            return_value=["profile1", "profile2"],
        ):
            result = self.command._get_valid_profiles()

        assert result == ["profile1", "profile2"]

    # ===== check aws credentials Tests =====

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    def test_check_aws_credentials_calls_guide_on_missing_file(self):
        """Test _check_aws_credentials guides setup when credentials file missing."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = (
                False
            )
            with patch.object(
                self.command, "_guide_credential_setup", return_value=False
            ) as mock_guide:
                result = self.command._check_aws_credentials()

            assert result is False
            mock_guide.assert_called_once()

    @pytest.mark.skipif(not AGENT_AVAILABLE, reason="telcocli_agent module not available")
    def test_check_aws_credentials_handles_parse_error(self):
        """Test _check_aws_credentials handles malformed credentials file."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value.__truediv__.return_value.__truediv__.return_value.exists.return_value = (
                True
            )
            with patch("configparser.ConfigParser") as mock_config:
                mock_config.return_value.read.side_effect = Exception("Parse error")
                with patch.object(
                    self.command, "_guide_credential_setup", return_value=False
                ) as mock_guide:
                    result = self.command._check_aws_credentials()

                assert result is False
                mock_guide.assert_called_once()
