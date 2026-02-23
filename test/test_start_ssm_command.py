"""Tests for Start SSM Command."""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.commands.start_ssm import StartSSMCommand
from telco_cli.exceptions.base_exception import TelcoCLIException


class TestStartSSMCommand:
    """Test cases for StartSSMCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return StartSSMCommand()

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.ssm_id = "mi-053192a526cfcec5c"
        return args

    @pytest.fixture
    def sample_instances(self):
        """Sample SSM instance data."""
        return [
            {
                "InstanceId": "mi-053192a526cfcec5c",
                "Name": "test-server",
                "PingStatus": "Online",
                "PlatformName": "Ubuntu",
            },
            {
                "InstanceId": "mi-1234567890abcdef0",
                "Name": "offline-server",
                "PingStatus": "ConnectionLost",
                "PlatformName": "Amazon Linux",
            },
        ]

    def test_command_properties(self, command):
        """Test command properties."""
        assert command.name == "start-ssm"
        assert command.description == "Start an SSM session to a managed instance"

    def test_register_arguments(self, command):
        """Test argument registration."""
        parser = Mock()
        command.register(parser)

        parser.add_argument.assert_called_once_with(
            "--ssm-id",
            required=True,
            help="SSM managed instance ID to connect to",
        )

    @patch("telco_cli.commands.start_ssm.subprocess.run")
    @patch("os.environ.get")
    @patch("telco_cli.commands.start_ssm.SSMService")
    def test_run_success_online_instance(
        self,
        mock_ssm_service_class,
        mock_env_get,
        mock_subprocess,
        command,
        mock_args,
        sample_instances,
    ):
        """Test successful execution with online instance."""

        def mock_env_side_effect(key, default=None):
            env_vars = {
                "AWS_PROFILE": "test-profile",
                "AWS_DEFAULT_REGION": "us-west-2",
            }
            return env_vars.get(key, default)

        mock_env_get.side_effect = mock_env_side_effect

        mock_service = Mock()
        mock_ssm_service_class.return_value = mock_service
        mock_service.list_managed_instances.return_value = sample_instances

        with patch("telco_cli.commands.start_ssm.console") as mock_console:
            command.run(mock_args)

        mock_service.list_managed_instances.assert_called_once_with("All")
        mock_console.print.assert_called_with(
            "🔗 [cyan]Starting SSM session to mi-053192a526cfcec5c...[/cyan]"
        )
        mock_subprocess.assert_called_once_with(
            [
                "aws",
                "ssm",
                "start-session",
                "--target",
                "mi-053192a526cfcec5c",
                "--profile",
                "test-profile",
                "--region",
                "us-west-2",
            ],
            check=True,
        )

    @patch("telco_cli.commands.start_ssm.subprocess.run")
    @patch("telco_cli.commands.start_ssm.SSMService")
    def test_run_success_offline_instance_warning(
        self, mock_ssm_service_class, mock_subprocess, command, mock_args, sample_instances
    ):
        """Test execution with offline instance shows warning."""
        mock_args.ssm_id = "mi-1234567890abcdef0"

        mock_service = Mock()
        mock_ssm_service_class.return_value = mock_service
        mock_service.list_managed_instances.return_value = sample_instances

        with patch("telco_cli.commands.start_ssm.console") as mock_console:
            command.run(mock_args)

        mock_console.print.assert_any_call(
            "⚠️ [yellow]Warning: Instance mi-1234567890abcdef0 status is ConnectionLost[/yellow]"
        )

    @patch("telco_cli.commands.start_ssm.SSMService")
    def test_run_instance_not_found(
        self, mock_ssm_service_class, command, mock_args, sample_instances
    ):
        """Test execution with non-existent instance."""
        mock_args.ssm_id = "mi-nonexistent"

        mock_service = Mock()
        mock_ssm_service_class.return_value = mock_service
        mock_service.list_managed_instances.return_value = sample_instances

        with patch("telco_cli.commands.start_ssm.console") as mock_console:
            with pytest.raises(SystemExit):
                command.run(mock_args)

        mock_console.print.assert_called_with(
            "❌ [red]Instance mi-nonexistent not found in SSM.[/red]"
        )

    @patch("telco_cli.commands.start_ssm.SSMService")
    def test_run_client_error(self, mock_ssm_service_class, command, mock_args):
        """Test execution with AWS client error."""
        mock_service = Mock()
        mock_ssm_service_class.return_value = mock_service
        mock_service.list_managed_instances.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeInstanceInformation",
        )

        with pytest.raises(TelcoCLIException):
            command.run(mock_args)

    @patch("telco_cli.commands.start_ssm.subprocess.run")
    def test_start_session_subprocess_error(self, mock_subprocess, command):
        """Test _start_session with subprocess error."""
        from subprocess import CalledProcessError

        mock_subprocess.side_effect = CalledProcessError(1, "aws")

        with pytest.raises(TelcoCLIException):
            command._start_session("mi-test")

    @patch("telco_cli.commands.start_ssm.subprocess.run")
    def test_start_session_file_not_found(self, mock_subprocess, command):
        """Test _start_session with AWS CLI not found."""
        mock_subprocess.side_effect = FileNotFoundError()

        with pytest.raises(TelcoCLIException) as exc_info:
            command._start_session("mi-test")

        assert "AWS CLI not found" in str(exc_info.value)
