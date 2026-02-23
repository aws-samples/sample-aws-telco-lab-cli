"""Unit tests for MonitoringService."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.services.monitoring import MonitoringService


class TestMonitoringService:
    """Test cases for MonitoringService."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("telco_cli.services.monitoring.boto3.client"):
            self.service = MonitoringService()

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_init(self, mock_boto3):
        """Test MonitoringService initialization."""
        service = MonitoringService()
        assert service is not None

        # Verify boto3 clients are created
        assert mock_boto3.call_count == 2
        mock_boto3.assert_any_call("cloudwatch")
        mock_boto3.assert_any_call("logs")

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_get_partner_metrics_success(self, mock_boto3):
        """Test successful partner metrics retrieval."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        # Mock CloudWatch response
        mock_cloudwatch.get_metric_statistics.return_value = {
            "Datapoints": [
                {"Timestamp": datetime.now(timezone.utc), "Sum": 100.0, "Unit": "Count"},
                {
                    "Timestamp": datetime.now(timezone.utc) - timedelta(hours=1),
                    "Sum": 85.0,
                    "Unit": "Count",
                },
            ]
        }

        service = MonitoringService()
        result = service.get_partner_metrics("test-partner", 24)

        assert result["PartnerName"] == "test-partner"
        assert result["TimeRange"] == "24 hours"
        assert len(result["Metrics"]) == 2
        assert "LastUpdated" in result

        # Verify CloudWatch API call
        mock_cloudwatch.get_metric_statistics.assert_called_once()
        call_args = mock_cloudwatch.get_metric_statistics.call_args[1]
        assert call_args["Namespace"] == "TelcoCLI/Partners"
        assert call_args["MetricName"] == "APICallCount"
        assert call_args["Dimensions"][0]["Name"] == "PartnerName"
        assert call_args["Dimensions"][0]["Value"] == "test-partner"
        assert call_args["Period"] == 3600
        assert call_args["Statistics"] == ["Sum"]

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_get_partner_metrics_aws_error(self, mock_boto3):
        """Test AWS error handling in get_partner_metrics."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        # Mock ClientError
        mock_cloudwatch.get_metric_statistics.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "GetMetricStatistics"
        )

        service = MonitoringService()

        with pytest.raises(TelcoCLIException) as exc_info:
            service.get_partner_metrics("test-partner")

        assert exc_info.value.error_code == ErrorCode.AWS_API_ERROR
        assert "Access denied" in str(exc_info.value)

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_get_partner_metrics_default_hours(self, mock_boto3):
        """Test get_partner_metrics with default hours parameter."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        mock_cloudwatch.get_metric_statistics.return_value = {"Datapoints": []}

        service = MonitoringService()
        result = service.get_partner_metrics("test-partner")

        assert result["TimeRange"] == "24 hours"

        # Verify time range calculation
        call_args = mock_cloudwatch.get_metric_statistics.call_args[1]
        start_time = call_args["StartTime"]
        end_time = call_args["EndTime"]
        time_diff = end_time - start_time
        assert abs(time_diff.total_seconds() - 24 * 3600) < 60  # Within 1 minute tolerance

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_put_custom_metric_success(self, mock_boto3):
        """Test successful custom metric publishing."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        service = MonitoringService()

        # Test without dimensions
        service.put_custom_metric("TestMetric", 42.5)

        mock_cloudwatch.put_metric_data.assert_called_once()
        call_args = mock_cloudwatch.put_metric_data.call_args[1]
        assert call_args["Namespace"] == "TelcoCLI/Custom"
        assert len(call_args["MetricData"]) == 1

        metric_data = call_args["MetricData"][0]
        assert metric_data["MetricName"] == "TestMetric"
        assert metric_data["Value"] == 42.5
        assert metric_data["Dimensions"] == []
        assert isinstance(metric_data["Timestamp"], datetime)

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_put_custom_metric_with_dimensions(self, mock_boto3):
        """Test custom metric publishing with dimensions."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        service = MonitoringService()

        dimensions = [
            {"Name": "Partner", "Value": "test-partner"},
            {"Name": "Region", "Value": "us-west-2"},
        ]

        service.put_custom_metric("TestMetric", 100.0, dimensions)

        call_args = mock_cloudwatch.put_metric_data.call_args[1]
        metric_data = call_args["MetricData"][0]
        assert metric_data["Dimensions"] == dimensions

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_put_custom_metric_aws_error(self, mock_boto3):
        """Test AWS error handling in put_custom_metric."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        # Mock ClientError
        mock_cloudwatch.put_metric_data.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterValue", "Message": "Invalid parameter"}},
            "PutMetricData",
        )

        service = MonitoringService()

        with pytest.raises(TelcoCLIException) as exc_info:
            service.put_custom_metric("TestMetric", 42.5)

        assert exc_info.value.error_code == ErrorCode.AWS_API_ERROR
        assert "Invalid parameter" in str(exc_info.value)

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_get_partner_metrics_custom_hours(self, mock_boto3):
        """Test get_partner_metrics with custom hours parameter."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        mock_cloudwatch.get_metric_statistics.return_value = {"Datapoints": []}

        service = MonitoringService()
        result = service.get_partner_metrics("test-partner", 48)

        assert result["TimeRange"] == "48 hours"

        # Verify time range calculation for 48 hours
        call_args = mock_cloudwatch.get_metric_statistics.call_args[1]
        start_time = call_args["StartTime"]
        end_time = call_args["EndTime"]
        time_diff = end_time - start_time
        assert abs(time_diff.total_seconds() - 48 * 3600) < 60  # Within 1 minute tolerance

    @patch("telco_cli.services.monitoring.boto3.client")
    def test_put_custom_metric_none_dimensions(self, mock_boto3):
        """Test put_custom_metric with None dimensions."""
        mock_cloudwatch = Mock()
        mock_logs = Mock()
        mock_boto3.side_effect = [mock_cloudwatch, mock_logs]

        service = MonitoringService()
        service.put_custom_metric("TestMetric", 42.5, None)

        call_args = mock_cloudwatch.put_metric_data.call_args[1]
        metric_data = call_args["MetricData"][0]
        assert metric_data["Dimensions"] == []
