# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Configure kubectl access to EKS cluster command."""

import argparse
import subprocess

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger
from telco_cli.utils.validation import validate_cluster_name

logger = get_logger(__name__)


class ConfigureEksAccessCommand(BaseCommand):
    """Configure kubectl access to EKS cluster using AWS profile."""

    @property
    def name(self) -> str:
        return "configure-eks-access"

    @property
    def description(self) -> str:
        return "Configure kubectl access to EKS cluster using AWS profile"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--cluster-name", required=True, help="EKS cluster name")
        parser.add_argument("--profile-name", required=True, help="AWS profile to use")
        parser.add_argument("--region", default="us-east-1", help="AWS region")
        parser.add_argument("--alias", help="kubectl context alias (default: cluster-name)")

    def run(self, args: argparse.Namespace) -> None:
        """Execute the configure EKS access command."""
        try:
            # Validate inputs
            if not validate_cluster_name(args.cluster_name):
                raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, "Invalid cluster name format")

            alias = args.alias or args.cluster_name

            # Configure kubectl context
            console.print(f"⚙️  Configuring kubectl for cluster: {args.cluster_name}")
            context_name = self._configure_kubectl_context(
                cluster_name=args.cluster_name,
                profile_name=args.profile_name,
                region=args.region,
                alias=alias,
            )

            # Test access
            console.print("🧪 Testing cluster access...")
            if self._test_cluster_access(context_name):
                console.print(f"✅ kubectl configured for cluster: {args.cluster_name}")
                console.print(f"🔧 Context: {context_name}")
                console.print(f"📋 Test with: kubectl --context {context_name} get nodes")
            else:
                console.print("❌ Failed to access cluster", style="error")
                raise TelcoCLIException(
                    ErrorCode.KUBECTL_ACCESS_DENIED, "Unable to access EKS cluster"
                )

        except TelcoCLIException:
            raise
        except Exception as e:
            logger.exception("Unexpected error in configure-eks-access")
            raise TelcoCLIException(ErrorCode.KUBECTL_CONFIG_FAILED, str(e))

    def _configure_kubectl_context(
        self, cluster_name: str, profile_name: str, region: str, alias: str
    ) -> str:
        """Configure kubectl context for EKS cluster."""
        cmd = [
            "aws",
            "eks",
            "update-kubeconfig",
            "--name",
            cluster_name,
            "--region",
            region,
            "--profile",
            profile_name,
            "--alias",
            alias,
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return alias
        except subprocess.CalledProcessError as e:
            raise TelcoCLIException(
                ErrorCode.KUBECTL_CONFIG_FAILED, f"Failed to configure kubectl: {e.stderr.decode()}"
            )

    def _test_cluster_access(self, context_name: str) -> bool:
        """Test kubectl access to cluster."""
        try:
            cmd = ["kubectl", "--context", context_name, "get", "nodes", "--no-headers"]
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
