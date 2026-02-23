"""Tests for EKS deployment service."""

import subprocess
import unittest
from unittest.mock import Mock, patch

from telco_cli.services.eks_deployment_service import EksDeploymentService


class TestEksDeploymentService(unittest.TestCase):
    """Test cases for EksDeploymentService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = EksDeploymentService()

    @patch("subprocess.run")
    def test_terraform_init_success(self, mock_run):
        """Test successful Terraform initialization."""
        mock_run.return_value = Mock(returncode=0)

        result = self.service._terraform_init()

        self.assertTrue(result["success"])
        mock_run.assert_called_once_with(
            ["terraform", "init"],
            cwd=self.service.terraform_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_terraform_init_failure(self, mock_run):
        """Test Terraform initialization failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "terraform", stderr="Init failed")

        result = self.service._terraform_init()

        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "TERRAFORM_INIT_FAILED")

    @patch("subprocess.run")
    def test_terraform_plan_success(self, mock_run):
        """Test successful Terraform plan."""
        mock_run.return_value = Mock(returncode=0)

        terraform_vars = {
            "cluster_name": "test-cluster",
            "aws_region": "us-east-1",
            "worker_instance_type": "m5.2xlarge",
            "desired_capacity": 2,
        }

        result = self.service._terraform_plan(terraform_vars)

        self.assertTrue(result["success"])
        # Verify terraform was called with correct parameters
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]  # Get the command list
        self.assertIn("terraform", call_args)
        self.assertIn("plan", call_args)
        self.assertIn("-var=cluster_name=test-cluster", call_args)
        self.assertIn("-var=aws_region=us-east-1", call_args)
        self.assertIn("-var=worker_instance_type=m5.2xlarge", call_args)

    @patch("subprocess.run")
    def test_terraform_apply_success(self, mock_run):
        """Test successful Terraform apply."""
        mock_run.return_value = Mock(returncode=0)

        result = self.service._terraform_apply()

        self.assertTrue(result["success"])
        mock_run.assert_called_once_with(
            ["terraform", "apply", "-auto-approve", "tfplan"],
            cwd=self.service.terraform_dir,
            capture_output=True,
            text=True,
            check=True,
        )

    @patch("subprocess.run")
    def test_destroy_cluster_success(self, mock_run):
        """Test successful cluster destruction."""
        mock_run.return_value = Mock(returncode=0)

        result = self.service.destroy_cluster("test-cluster")

        self.assertTrue(result["success"])
        self.assertIn("destroyed successfully", result["message"])

    @patch("os.path.exists")
    def test_validate_deployment_parameters_missing_terraform_dir(self, mock_exists):
        """Test validation with missing Terraform directory."""
        mock_exists.return_value = False

        terraform_vars = {
            "cluster_name": "test-cluster",
            "aws_region": "us-east-1",
            "worker_instance_type": "m5.2xlarge",
            "desired_capacity": 1,
        }

        result = self.service._validate_deployment_parameters(terraform_vars)

        self.assertFalse(result["success"])
        self.assertIn("Terraform directory not found", result["error"])

    @patch("os.path.exists")
    def test_validate_deployment_parameters_success(self, mock_exists):
        """Test successful parameter validation."""
        mock_exists.return_value = True

        terraform_vars = {
            "cluster_name": "test-cluster",
            "aws_region": "us-east-1",
            "worker_instance_type": "m5.2xlarge",
            "desired_capacity": 1,
        }

        result = self.service._validate_deployment_parameters(terraform_vars)

        self.assertTrue(result["success"])
        self.assertEqual(result["cluster_name"], "test-cluster")

    def test_validate_deployment_parameters_invalid_cluster_name(self):
        """Test validation with invalid cluster name."""
        terraform_vars = {
            "cluster_name": "a" * 101,  # Too long
            "aws_region": "us-east-1",
            "worker_instance_type": "m5.2xlarge",
            "desired_capacity": 1,
        }

        result = self.service._validate_deployment_parameters(terraform_vars)

        self.assertFalse(result["success"])

    @patch.object(EksDeploymentService, "_terraform_init")
    @patch.object(EksDeploymentService, "_terraform_plan")
    @patch.object(EksDeploymentService, "_terraform_apply")
    def test_deploy_full_cluster_success(self, mock_apply, mock_plan, mock_init):
        """Test successful full cluster deployment."""
        mock_init.return_value = {"success": True}
        mock_plan.return_value = {"success": True}
        mock_apply.return_value = {"success": True}

        terraform_vars = {
            "cluster_name": "test-cluster",
            "aws_region": "us-east-1",
            "worker_instance_type": "m5.2xlarge",
            "desired_capacity": 2,
        }

        result = self.service.deploy_full_cluster(
            terraform_vars=terraform_vars,
            dry_run=False,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["cluster_name"], "test-cluster")
        self.assertEqual(result["region"], "us-east-1")

    @patch.object(EksDeploymentService, "_validate_deployment_parameters")
    def test_deploy_full_cluster_dry_run(self, mock_validate):
        """Test dry run mode."""
        mock_validate.return_value = {"success": True, "cluster_name": "test-cluster"}

        terraform_vars = {
            "cluster_name": "test-cluster",
            "aws_region": "us-east-1",
            "worker_instance_type": "m5.2xlarge",
            "desired_capacity": 1,
        }

        result = self.service.deploy_full_cluster(
            terraform_vars=terraform_vars,
            dry_run=True,
        )

        self.assertTrue(result["success"])
        mock_validate.assert_called_once()

    @patch.object(EksDeploymentService, "_terraform_init")
    @patch.object(EksDeploymentService, "_terraform_plan")
    @patch.object(EksDeploymentService, "_terraform_apply")
    def test_deploy_full_cluster_skip_observability(self, mock_apply, mock_plan, mock_init):
        """Test deployment with observability skipped."""
        mock_init.return_value = {"success": True}
        mock_plan.return_value = {"success": True}
        mock_apply.return_value = {"success": True}

        terraform_vars = {
            "cluster_name": "test-cluster",
            "aws_region": "us-east-1",
            "worker_instance_type": "m5.2xlarge",
            "desired_capacity": 1,
            "deploy_observability": False,
        }

        result = self.service.deploy_full_cluster(
            terraform_vars=terraform_vars,
            dry_run=False,
        )

        self.assertTrue(result["success"])
        # Verify terraform plan was called with the terraform_vars dict
        mock_plan.assert_called_once_with(terraform_vars)


if __name__ == "__main__":
    unittest.main()
