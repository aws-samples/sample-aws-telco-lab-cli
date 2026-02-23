"""Tests for List Test Servers Command."""

from unittest.mock import Mock, PropertyMock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.commands.list_test_servers import ListTestServersCommand
from telco_cli.exceptions.base_exception import TelcoCLIException


class TestListTestServersCommand:
    """Test cases for ListTestServersCommand."""

    @pytest.fixture
    def command(self):
        """Create command instance."""
        return ListTestServersCommand()

    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.status = "All"
        args.output = "table"
        args.show_nic_detail = False
        return args

    @pytest.fixture
    def sample_instances(self):
        """Sample SSM instance data."""
        return [
            {
                "InstanceId": "i-1234567890abcdef0",
                "Name": "test-server-1",
                "PingStatus": "Online",
                "PlatformName": "Amazon Linux",
                "IPAddress": "10.0.1.100",
            },
            {
                "InstanceId": "i-0987654321fedcba0",
                "Name": "test-server-2",
                "PingStatus": "Offline",
                "PlatformName": "Ubuntu",
                "IPAddress": "10.0.1.101",
            },
        ]

    def test_command_properties(self, command):
        """Test command properties."""
        assert command.name == "list-test-servers"
        assert command.description == "List all SSM managed test servers"

    def test_register_arguments(self, command):
        """Test argument registration."""
        parser = Mock()
        command.register(parser)

        assert parser.add_argument.call_count == 3
        parser.add_argument.assert_any_call(
            "--status",
            choices=["Online", "Offline", "All"],
            default="All",
            help="Filter servers by SSM status",
        )
        parser.add_argument.assert_any_call(
            "--output",
            choices=["json", "table"],
            default="table",
            help="Output format (default: table)",
        )

    def test_run_success_table_output(self, command, mock_args, sample_instances):
        """Test successful execution with table output."""
        mock_service = Mock()
        mock_service.list_managed_instances.return_value = sample_instances

        with patch.object(
            type(command), "instance_service", new_callable=PropertyMock, return_value=mock_service
        ):
            with patch.object(command, "_display_servers_table") as mock_display:
                command.run(mock_args)

        mock_service.list_managed_instances.assert_called_once_with("All")
        mock_display.assert_called_once_with(sample_instances)

    def test_run_success_json_output(self, command, mock_args, sample_instances):
        """Test successful execution with JSON output."""
        mock_args.output = "json"
        mock_service = Mock()
        mock_service.list_managed_instances.return_value = sample_instances

        with patch.object(
            type(command), "instance_service", new_callable=PropertyMock, return_value=mock_service
        ):
            with patch.object(command, "_display_servers_json") as mock_display:
                command.run(mock_args)

        mock_display.assert_called_once_with(sample_instances)

    def test_run_with_status_filter(self, command, mock_args):
        """Test execution with status filter."""
        mock_args.status = "Online"
        mock_service = Mock()
        mock_service.list_managed_instances.return_value = []

        with patch.object(
            type(command), "instance_service", new_callable=PropertyMock, return_value=mock_service
        ):
            with patch.object(command, "_display_servers_table"):
                command.run(mock_args)

        mock_service.list_managed_instances.assert_called_once_with("Online")

    def test_run_client_error(self, command, mock_args):
        """Test execution with AWS client error."""
        mock_service = Mock()
        mock_service.list_managed_instances.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeInstanceInformation",
        )

        with patch.object(
            type(command), "instance_service", new_callable=PropertyMock, return_value=mock_service
        ):
            with pytest.raises(TelcoCLIException):
                command.run(mock_args)

    def test_display_servers_table_empty(self, command):
        """Test table display with empty server list."""
        with patch.object(command.console, "print") as mock_print:
            command._display_servers_table([])

        mock_print.assert_called_with("📭 [yellow]No SSM managed servers found.[/yellow]")

    def test_display_servers_table_with_data(self, command, sample_instances):
        """Test table display with server data."""
        with patch.object(command.console, "print") as mock_print:
            command._display_servers_table(sample_instances)

        assert mock_print.call_count == 2  # Title and table

    def test_display_servers_json_empty(self, command):
        """Test JSON display with empty server list."""
        with patch.object(command.console, "print") as mock_print:
            command._display_servers_json([])

        mock_print.assert_called_with("📭 [yellow]No SSM managed servers found.[/yellow]")

    def test_display_servers_json_with_data(self, command, sample_instances):
        """Test JSON display with server data."""
        with (
            patch.object(command.console, "print") as mock_print,
            patch("builtins.print") as mock_builtin_print,
        ):
            command._display_servers_json(sample_instances)

        mock_print.assert_called_once()  # Title
        mock_builtin_print.assert_called_once()  # JSON output
