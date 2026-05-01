"""Tests for deploy EKS full command."""

import argparse
import unittest
from unittest.mock import Mock, patch

from telco_cli.commands.deploy_eks_full import DeployEksFullCommand
from telco_cli.exceptions import ErrorCode, TelcoCLIException


class TestDeployEksFullCommand(unittest.TestCase):
    """Test cases for DeployEksFullCommand."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = DeployEksFullCommand()

    def test_command_properties(self):
        """Test command properties."""
        self.assertEqual(self.command.name, "deploy-eks-full")
        self.assertEqual(
            self.command.description, "Deploy complete EKS infrastructure using Terraform modules"
        )

    def _create_test_args(self, **overrides):
        """Create test args namespace with all required attributes."""
        defaults = {
            # Core parameters
            "cluster_name": "test-cluster",
            "aws_region": "us-east-1",
            "aws_profile": "default",
            "terraform_dir": "src/telco_cli/templates/terraform/eks",
            # Infrastructure control
            "deploy_vpc": True,
            "deploy_eks": True,
            "deploy_worker_nodes": True,
            "deploy_observability": True,
            # Existing infrastructure
            "existing_vpc_id": None,
            "existing_key_pair_name": None,
            # Cluster configuration
            "cluster_version": "1.32",
            "vpc_cidr": "10.3.0.0/16",
            "edge_subnet_cidr": "100.77.4.0/24",
            "environment": "test",
            # Worker configuration
            "worker_instance_type": "m5.2xlarge",
            "outpost_instance_type": "bmn-sf2.metal-32xl",
            "desired_capacity": 1,
            "worker_node_volume_size": 100,
            # Outposts configuration
            "use_outposts": False,
            "outpost_id": None,
            "outpost_account_id": None,
            # Dedicated host configuration
            "use_dedicated_host": False,
            "dedicated_host_id": None,
            # Security
            "grafana_admin_password": None,
            # Advanced options
            "use_cilium": False,
            "install_observability_addons": True,
            "install_prometheus_addons": True,
            # Operational parameters
            "dry_run": False,
        }
        # Keep this test helper resilient to argument shape changes by starting from
        # real parser defaults, then overriding with explicit test values.
        parser = argparse.ArgumentParser()
        self.command.register(parser)
        parsed = vars(parser.parse_args(["--cluster-name", "test-cluster"]))
        parsed.update(defaults)
        parsed.update(overrides)
        return argparse.Namespace(**parsed)

    def test_register_arguments(self):
        """Test argument registration."""
        parser = argparse.ArgumentParser()
        self.command.register(parser)

        # Test required arguments
        with self.assertRaises(SystemExit):
            parser.parse_args([])

        # Test successful parsing with required args
        args = parser.parse_args(["--cluster-name", "test-cluster"])

        self.assertEqual(args.cluster_name, "test-cluster")
        self.assertEqual(args.aws_region, "us-east-1")  # default
        self.assertEqual(args.worker_instance_type, "m5.2xlarge")  # default

    @patch("telco_cli.commands.deploy_eks_full.EksDeploymentService")
    @patch("telco_cli.utils.validation.validate_cluster_name")
    @patch("telco_cli.utils.validation.validate_vpc_cidr")
    @patch("telco_cli.utils.validation.validate_aws_account_id")
    def test_run_success_dry_run(
        self, mock_validate_account, mock_validate_cidr, mock_validate_name, mock_service_class
    ):
        """Test successful dry run execution."""
        # Setup mocks
        mock_validate_name.return_value = (True, "")
        mock_validate_cidr.return_value = (True, "")
        mock_validate_account.return_value = True

        mock_service = Mock()
        mock_service.deploy_full_cluster.return_value = {
            "success": True,
            "cluster_name": "test-cluster",
            "region": "us-east-1",
            "instance_type": "m5.2xlarge",
            "node_count": 1,
            "templates": ["terraform/eks/main.tf"],
        }
        mock_service_class.return_value = mock_service

        # Create args
        args = self._create_test_args(dry_run=True)

        # Execute command
        self.command.run(args)

        # Verify service was called correctly
        mock_service.deploy_full_cluster.assert_called_once()
        call_args = mock_service.deploy_full_cluster.call_args
        kwargs = call_args[1]
        self.assertEqual(kwargs["dry_run"], True)
        self.assertIsNotNone(kwargs["terraform_vars"])
        self.assertIsNotNone(kwargs["terraform_dir"])

    @patch("telco_cli.commands.deploy_eks_full.EksDeploymentService")
    @patch("telco_cli.utils.validation.validate_cluster_name")
    @patch("telco_cli.utils.validation.validate_vpc_cidr")
    @patch("telco_cli.utils.validation.validate_aws_account_id")
    def test_run_success_deploy(
        self, mock_validate_account, mock_validate_cidr, mock_validate_name, mock_service_class
    ):
        """Test successful deployment execution."""
        # Setup mocks
        mock_validate_name.return_value = (True, "")
        mock_validate_cidr.return_value = (True, "")
        mock_validate_account.return_value = True

        mock_service = Mock()
        mock_service.deploy_full_cluster.return_value = {
            "success": True,
            "cluster_name": "test-cluster",
            "region": "us-east-1",
            "vpc_stack": "terraform-vpc-test-cluster",
            "eks_stack": "terraform-eks-test-cluster",
            "worker_stack": "terraform-workers-test-cluster",
        }
        mock_service_class.return_value = mock_service

        # Create args
        args = self._create_test_args(desired_capacity=2)

        # Execute command
        self.command.run(args)

        # Verify service was called correctly
        mock_service.deploy_full_cluster.assert_called_once()
        call_args = mock_service.deploy_full_cluster.call_args
        kwargs = call_args[1]
        self.assertEqual(kwargs["dry_run"], False)
        self.assertIsNotNone(kwargs["terraform_vars"])
        self.assertIsNotNone(kwargs["terraform_dir"])

    @patch("telco_cli.commands.deploy_eks_full.validate_cluster_name")
    def test_run_invalid_cluster_name(self, mock_validate_name):
        """Test execution with invalid cluster name."""
        mock_validate_name.return_value = (False, "Invalid cluster name")

        args = self._create_test_args(cluster_name="invalid-cluster-name-too-long")

        with self.assertRaises(TelcoCLIException) as context:
            self.command.run(args)

        self.assertEqual(context.exception.error_code, ErrorCode.VALIDATION_ERROR)

    @patch("telco_cli.commands.deploy_eks_full.EksDeploymentService")
    @patch("telco_cli.utils.validation.validate_cluster_name")
    @patch("telco_cli.utils.validation.validate_vpc_cidr")
    def test_run_deployment_failure(
        self, mock_validate_cidr, mock_validate_name, mock_service_class
    ):
        """Test deployment failure handling."""
        # Setup mocks
        mock_validate_name.return_value = (True, "")
        mock_validate_cidr.return_value = (True, "")

        mock_service = Mock()
        mock_service.deploy_full_cluster.return_value = {
            "success": False,
            "error": "Terraform apply failed",
        }
        mock_service_class.return_value = mock_service

        args = argparse.Namespace(
            cluster_name="test-cluster",
            region="us-east-1",
            instance_type="m5.2xlarge",
            desired_capacity=1,
            target_account_id=None,
            vpc_cidr="10.3.0.0/16",
            dry_run=False,
        )

        with self.assertRaises(TelcoCLIException) as context:
            self.command.run(args)

        self.assertEqual(context.exception.error_code, ErrorCode.EKS_DEPLOYMENT_FAILED)

    @patch("telco_cli.commands.deploy_eks_full.EksDeploymentService")
    @patch("telco_cli.utils.validation.validate_cluster_name")
    @patch("telco_cli.utils.validation.validate_vpc_cidr")
    @patch("telco_cli.utils.validation.validate_aws_account_id")
    def test_run_success_skip_observability(
        self, mock_validate_account, mock_validate_cidr, mock_validate_cluster, mock_service_class
    ):
        """Test successful deployment with observability skipped."""
        mock_validate_cluster.return_value = (True, "")
        mock_validate_cidr.return_value = (True, "")
        mock_validate_account.return_value = True

        mock_service = Mock()
        mock_service.deploy_full_cluster.return_value = {
            "success": True,
            "cluster_name": "test-cluster",
            "region": "us-east-1",
            "vpc_stack": "terraform-vpc-test-cluster",
            "eks_stack": "terraform-eks-test-cluster",
            "worker_stack": "terraform-workers-test-cluster",
        }
        mock_service_class.return_value = mock_service

        args = self._create_test_args(deploy_observability=False)

        self.command.run(args)

        # Verify service was called correctly
        mock_service.deploy_full_cluster.assert_called_once()
        call_args = mock_service.deploy_full_cluster.call_args
        kwargs = call_args[1]
        self.assertEqual(kwargs["dry_run"], False)
        self.assertIsNotNone(kwargs["terraform_vars"])
        # Check that deploy_observability is False in terraform_vars
        self.assertEqual(kwargs["terraform_vars"]["deploy_observability"], False)

    @patch("telco_cli.utils.validation.validate_aws_account_id")
    @patch("telco_cli.utils.validation.validate_cluster_name")
    @patch("telco_cli.utils.validation.validate_vpc_cidr")
    def test_run_invalid_account_id(
        self, mock_validate_cidr, mock_validate_name, mock_validate_account
    ):
        """Test execution with invalid AWS account ID."""
        mock_validate_name.return_value = (True, "")
        mock_validate_cidr.return_value = (True, "")
        mock_validate_account.return_value = False

        args = self._create_test_args()

        with self.assertRaises(TelcoCLIException) as context:
            self.command.run(args)

        self.assertEqual(context.exception.error_code, ErrorCode.EKS_CLUSTER_DEPLOYMENT_FAILED)


if __name__ == "__main__":
    unittest.main()
