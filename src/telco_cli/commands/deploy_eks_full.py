# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Deploy complete EKS infrastructure command."""

import argparse

from telco_cli.exceptions import ErrorCode, TelcoCLIException
from telco_cli.services.eks_deployment_service import EksDeploymentService
from telco_cli.types.base_command import BaseCommand
from telco_cli.utils import console, get_logger
from telco_cli.utils.validation import validate_cluster_name, validate_vpc_cidr

logger = get_logger(__name__)


class DeployEksFullCommand(BaseCommand):
    """Deploy complete EKS infrastructure (VPC + Cluster + Workers)."""

    @property
    def name(self) -> str:
        return "deploy-eks-full"

    @property
    def description(self) -> str:
        return "Deploy complete EKS infrastructure using Terraform modules"

    def register(self, parser: argparse.ArgumentParser) -> None:
        """Register command arguments."""
        # Core parameters
        parser.add_argument("--cluster-name", required=True, help="EKS cluster name")
        parser.add_argument("--aws-region", default="us-east-1", help="AWS region")
        parser.add_argument("--aws-profile", default="default", help="AWS profile to use")
        parser.add_argument(
            "--terraform-dir",
            default="src/telco_cli/templates/terraform/eks",
            help="Terraform directory path",
        )

        # Infrastructure control
        parser.add_argument("--deploy-vpc", action="store_true", help="Deploy new VPC")
        parser.add_argument("--deploy-eks", action="store_true", help="Deploy new EKS cluster")
        parser.add_argument(
            "--deploy-worker-nodes", action="store_true", help="Deploy worker nodes"
        )
        parser.add_argument(
            "--deploy-observability",
            action="store_true",
            default=True,
            help="Deploy observability stack",
        )

        # Existing infrastructure
        parser.add_argument("--existing-vpc-id", help="Use existing VPC ID")
        parser.add_argument("--existing-key-pair-name", help="Use existing key pair")

        # Cluster configuration
        parser.add_argument("--cluster-version", default="1.32", help="EKS cluster version")
        parser.add_argument("--vpc-cidr", default="100.77.0.0/16", help="VPC CIDR block")
        parser.add_argument("--edge-subnet-cidr", default="100.77.4.0/24", help="Edge subnet CIDR")

        # Worker configuration
        parser.add_argument(
            "--worker-instance-type", default="m5.2xlarge", help="Worker instance type"
        )
        parser.add_argument(
            "--outpost-instance-type", default="bmn-sf2.metal-32xl", help="Outpost instance type"
        )
        parser.add_argument("--desired-capacity", type=int, default=1, help="Desired worker nodes")
        parser.add_argument(
            "--worker-node-volume-size", type=int, default=100, help="Worker node EBS volume size"
        )

        # Outposts configuration
        parser.add_argument("--use-outposts", action="store_true", help="Deploy on Outposts")
        parser.add_argument("--outpost-id", help="Outpost ID (required if use-outposts)")
        parser.add_argument(
            "--outpost-account-id", help="Outpost account ID for RAM shared Outposts"
        )

        # Dedicated host configuration
        parser.add_argument("--use-dedicated-host", action="store_true", help="Use dedicated host")
        parser.add_argument(
            "--dedicated-host-id", help="Dedicated host ID (required if use-dedicated-host)"
        )

        # Security
        parser.add_argument(
            "--grafana-admin-password",
            help="Grafana admin password (auto-generated if not provided)",
        )

        # Advanced options
        parser.add_argument(
            "--use-cilium", action="store_true", help="Use Cilium CNI instead of VPC CNI"
        )
        parser.add_argument(
            "--install-observability-addons",
            action="store_true",
            default=True,
            help="Install CloudWatch observability",
        )
        parser.add_argument(
            "--install-prometheus-addons",
            action="store_true",
            default=True,
            help="Install Prometheus monitoring",
        )

        # Operational parameters
        parser.add_argument("--dry-run", action="store_true", help="Validate without deploying")
        parser.add_argument("--environment", default="test", help="Environment name")

    def run(self, args: argparse.Namespace) -> None:
        """Execute the deploy EKS full command."""
        try:
            # Validate inputs
            is_valid, error_msg = validate_cluster_name(args.cluster_name)
            if not is_valid:
                raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, error_msg)

            is_valid, error_msg = validate_vpc_cidr(args.vpc_cidr)
            if not is_valid:
                raise TelcoCLIException(ErrorCode.VALIDATION_ERROR, error_msg)

            # Validate Outposts configuration
            if args.use_outposts and not args.outpost_id:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR, "outpost_id required when use_outposts=true"
                )

            # Validate dedicated host configuration
            if args.use_dedicated_host and not args.dedicated_host_id:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR,
                    "dedicated_host_id required when use_dedicated_host=true",
                )

            # Validate existing VPC configuration
            if not args.deploy_vpc and not args.existing_vpc_id:
                raise TelcoCLIException(
                    ErrorCode.VALIDATION_ERROR, "existing_vpc_id required when deploy_vpc=false"
                )

            # Initialize service
            service = EksDeploymentService()

            # Build Terraform variables matching new structure
            terraform_vars = {
                # AWS Configuration
                "aws_region": args.aws_region,
                "aws_profile": args.aws_profile,
                # Infrastructure Control
                "deploy_vpc": args.deploy_vpc,
                "deploy_eks": args.deploy_eks,
                "deploy_worker_nodes": args.deploy_worker_nodes,
                "deploy_observability": args.deploy_observability,
                # Existing Infrastructure
                "existing_vpc_id": args.existing_vpc_id or "",
                "existing_key_pair_name": args.existing_key_pair_name or "",
                # Cluster Configuration
                "cluster_name": args.cluster_name,
                "cluster_version": args.cluster_version,
                "environment": args.environment,
                # Network Configuration
                "vpc_cidr": args.vpc_cidr,
                "edge_subnet_cidr": args.edge_subnet_cidr,
                # Worker Configuration
                "worker_instance_type": args.worker_instance_type,
                "outpost_instance_type": args.outpost_instance_type,
                "desired_capacity": args.desired_capacity,
                "worker_node_volume_size": args.worker_node_volume_size,
                # Outposts Configuration
                "use_outposts": args.use_outposts,
                "outpost_id": args.outpost_id or "",
                "outpost_account_id": args.outpost_account_id or "",
                # Dedicated Host Configuration
                "use_dedicated_host": args.use_dedicated_host,
                "dedicated_host_id": args.dedicated_host_id or "",
                # Security
                "grafana_admin_password": args.grafana_admin_password or "",
                # Advanced Options
                "use_cilium": args.use_cilium,
                "install_observability_addons": args.install_observability_addons,
                "install_prometheus_addons": args.install_prometheus_addons,
            }

            # Use service interface
            result = service.deploy_full_cluster(
                terraform_dir=args.terraform_dir,
                terraform_vars=terraform_vars,
                dry_run=args.dry_run,
            )

            if result["success"]:
                if args.dry_run:
                    console.print("✅ Configuration validation passed")
                    console.print("📋 Terraform configuration:")
                    console.print(f"  • Cluster: {args.cluster_name}")
                    console.print(f"  • Region: {args.aws_region}")
                    console.print(f"  • Deploy VPC: {args.deploy_vpc}")
                    console.print(f"  • Deploy EKS: {args.deploy_eks}")
                    console.print(f"  • Deploy Workers: {args.deploy_worker_nodes}")
                    console.print(f"  • Instance Type: {args.worker_instance_type}")
                    console.print(f"  • Desired Capacity: {args.desired_capacity}")
                else:
                    console.print("✅ EKS deployment complete!")
                    console.print(f"🎯 Cluster: {result.get('cluster_name', args.cluster_name)}")
                    console.print(f"🌍 Region: {args.aws_region}")
                    if result.get("vpc_id"):
                        console.print(f"🌐 VPC: {result['vpc_id']}")
                    if result.get("cluster_endpoint"):
                        console.print(f"🔗 Endpoint: {result['cluster_endpoint']}")
            else:
                error_msg = result.get("error", "Unknown error")
                raise TelcoCLIException(ErrorCode.EKS_DEPLOYMENT_FAILED, error_msg)

        except TelcoCLIException:
            raise
        except Exception as e:
            logger.exception("Unexpected error in deploy-eks-full")
            raise TelcoCLIException(ErrorCode.EKS_DEPLOYMENT_FAILED, str(e))
