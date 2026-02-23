# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Start SSM Session Command implementation."""

import argparse
import subprocess
import sys

from botocore.exceptions import ClientError

from telco_cli.exceptions.base_exception import TelcoCLIException
from telco_cli.exceptions.error_codes import ErrorCode
from telco_cli.services.ssm_service import SSMService
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger

logger = get_logger(__name__)


class StartSSMCommand(BaseCommand):
    """Start an SSM session to a managed instance."""

    def __init__(self):
        self._ssm_service = None

    @property
    def ssm_service(self) -> SSMService:
        """Lazy initialization of SSM service."""
        if self._ssm_service is None:
            self._ssm_service = SSMService()
        return self._ssm_service

    @property
    def name(self) -> str:
        return "start-ssm"

    @property
    def description(self) -> str:
        return "Start an SSM session to a managed instance"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument(
            "--ssm-id",
            required=True,
            help="SSM managed instance ID to connect to",
        )

    def run(self, args: argparse.Namespace) -> None:
        """Execute the start SSM session command."""
        try:
            logger.info(f"Starting SSM session to instance: {args.ssm_id}")

            # Verify instance exists and is online
            instances = self.ssm_service.list_managed_instances("All")
            target_instance = next(
                (inst for inst in instances if inst.get("InstanceId") == args.ssm_id), None
            )

            if not target_instance:
                console.print(f"❌ [red]Instance {args.ssm_id} not found in SSM.[/red]")
                sys.exit(1)

            status = target_instance.get("PingStatus", "Unknown")
            if status != "Online":
                console.print(
                    f"⚠️ [yellow]Warning: Instance {args.ssm_id} status is {status}[/yellow]"
                )

            console.print(f"🔗 [cyan]Starting SSM session to {args.ssm_id}...[/cyan]")

            # Start SSM session using AWS CLI
            self._start_session(args.ssm_id)

        except ClientError as e:
            logger.error(f"AWS error starting SSM session: {e}")
            raise TelcoCLIException(ErrorCode.AWS_API_ERROR, str(e))
        except Exception as e:
            logger.exception("Failed to start SSM session")
            raise TelcoCLIException(ErrorCode.UNKNOWN_ERROR, str(e))

    def _start_session(self, instance_id: str) -> None:
        """Start SSM session using AWS CLI."""
        import os

        cmd = ["aws", "ssm", "start-session", "--target", instance_id]

        # Add profile and region from environment if available
        aws_profile = os.environ.get("AWS_PROFILE")
        if aws_profile:
            cmd.extend(["--profile", aws_profile])
        aws_region = os.environ.get("AWS_DEFAULT_REGION")
        if aws_region:
            cmd.extend(["--region", aws_region])

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise TelcoCLIException(
                ErrorCode.COMMAND_EXECUTION_ERROR, f"Failed to start SSM session: {e}"
            )
        except FileNotFoundError:
            raise TelcoCLIException(
                ErrorCode.COMMAND_EXECUTION_ERROR,
                "AWS CLI not found. Please install AWS CLI and Session Manager plugin.",
            )
