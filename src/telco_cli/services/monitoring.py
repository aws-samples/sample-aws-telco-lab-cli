# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""AWS CloudWatch monitoring service for TelcoCLI."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.utils import get_logger

logger = get_logger(__name__)


class MonitoringService:
    """AWS CloudWatch monitoring service."""

    def __init__(self):
        """Initialize the monitoring service."""
        self.cloudwatch = boto3.client("cloudwatch")
        self.logs = boto3.client("logs")

    def get_partner_metrics(self, partner_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get CloudWatch metrics for a partner."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)

            # Get basic metrics
            metrics = self.cloudwatch.get_metric_statistics(
                Namespace="TelcoCLI/Partners",
                MetricName="APICallCount",
                Dimensions=[{"Name": "PartnerName", "Value": partner_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=["Sum"],
            )

            return {
                "PartnerName": partner_name,
                "TimeRange": f"{hours} hours",
                "Metrics": metrics.get("Datapoints", []),
                "LastUpdated": end_time.isoformat(),
            }

        except ClientError as e:
            logger.error(f"Failed to get partner metrics: {e}")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, str(e))

    def put_custom_metric(
        self, metric_name: str, value: float, dimensions: Optional[List[Dict[str, str]]] = None
    ) -> None:
        """Put a custom metric to CloudWatch."""
        try:
            self.cloudwatch.put_metric_data(
                Namespace="TelcoCLI/Custom",
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Timestamp": datetime.now(timezone.utc),
                        "Dimensions": dimensions or [],
                    }
                ],
            )
            logger.info(f"Published metric: {metric_name} = {value}")

        except ClientError as e:
            logger.error(f"Failed to put metric: {e}")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, str(e))
