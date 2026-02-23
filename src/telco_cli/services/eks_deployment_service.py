# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""EKS deployment service using Terraform templates."""

import os
import re
import subprocess
from typing import Any, Dict, Optional

from telco_cli.utils import get_logger

logger = get_logger(__name__)

# SECURITY: Patterns for validating terraform variable names and values
# Prevents command injection through terraform -var arguments
SAFE_VAR_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
# Allow alphanumeric, common punctuation, but reject shell metacharacters
SAFE_VAR_VALUE_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.\/\s\:\,\[\]\{\}\"\']+$")
MAX_VAR_VALUE_LENGTH = 1000


class EksDeploymentService:
    """Service for deploying EKS infrastructure using Terraform."""

    def __init__(self):
        """Initialize the EKS deployment service."""
        import os

        # Use package-relative path for terraform templates
        package_dir = os.path.dirname(os.path.dirname(__file__))  # telco_cli directory
        self.terraform_dir = os.path.join(package_dir, "templates", "terraform", "eks")
        logger.info(f"Using Terraform directory: {self.terraform_dir}")

    def deploy_full_cluster(
        self,
        terraform_dir: Optional[str] = None,
        terraform_vars: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Deploy complete EKS infrastructure using Terraform.

        Args:
            terraform_dir: Path to Terraform configuration directory
            terraform_vars: Dictionary of Terraform variables
            dry_run: If True, validate parameters without deploying

        Returns:
            Dict containing deployment status and details
        """
        try:
            # Use provided terraform_dir or default
            if terraform_dir:
                self.terraform_dir = terraform_dir

            terraform_vars = terraform_vars or {}
            cluster_name = terraform_vars.get("cluster_name", "unknown")

            if dry_run:
                logger.info("Dry run mode - validating parameters only")
                return self._validate_deployment_parameters(terraform_vars)

            logger.info(f"Starting EKS deployment using Terraform for cluster: {cluster_name}")

            # Initialize Terraform
            init_result = self._terraform_init()
            if not init_result["success"]:
                return init_result

            # Plan deployment
            plan_result = self._terraform_plan(terraform_vars)
            if not plan_result["success"]:
                return plan_result

            # Apply deployment
            apply_result = self._terraform_apply()
            if not apply_result["success"]:
                return apply_result

            logger.info(f"EKS deployment completed successfully for cluster: {cluster_name}")
            return {
                "success": True,
                "cluster_name": cluster_name,
                "region": terraform_vars.get("aws_region", "unknown"),
                "instance_type": terraform_vars.get("worker_instance_type", "unknown"),
                "node_count": terraform_vars.get("desired_capacity", 0),
            }

        except Exception as e:
            logger.error(f"EKS deployment failed: {str(e)}")
            return {"success": False, "error": str(e), "error_code": "EKS_DEPLOYMENT_FAILED"}

    def _terraform_init(self) -> Dict[str, Any]:
        """Initialize Terraform in the terraform/eks directory."""
        try:
            logger.info("Initializing Terraform...")
            subprocess.run(
                ["terraform", "init"],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return {"success": True}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error_code": "TERRAFORM_INIT_FAILED", "error": e.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _terraform_plan(self, terraform_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Plan Terraform deployment with variables.

        SECURITY: Validates all terraform variable names and values to prevent
        command injection through -var arguments.
        """
        try:
            logger.info("Planning Terraform deployment...")

            # Build terraform variables
            tf_vars = ["terraform", "plan"]

            # SECURITY: Validate and add variables from terraform_vars dict
            for key, value in terraform_vars.items():
                # Validate variable name
                if not SAFE_VAR_NAME_PATTERN.match(key):
                    return {
                        "success": False,
                        "error": f"Invalid terraform variable name: {key}. "
                        "Variable names must start with a letter or underscore "
                        "and contain only alphanumeric characters and underscores.",
                    }

                if value:  # Only add non-empty values
                    str_value = str(value)

                    # Validate variable value length
                    if len(str_value) > MAX_VAR_VALUE_LENGTH:
                        return {
                            "success": False,
                            "error": f"Terraform variable '{key}' value too long "
                            f"(max {MAX_VAR_VALUE_LENGTH} characters).",
                        }

                    # Validate variable value doesn't contain shell metacharacters
                    # Note: We allow some special chars needed for terraform values
                    if not SAFE_VAR_VALUE_PATTERN.match(str_value):
                        # Log sanitized version for debugging
                        logger.warning(f"Potentially unsafe terraform variable value for '{key}'")
                        return {
                            "success": False,
                            "error": f"Invalid characters in terraform variable '{key}'. "
                            "Values must not contain shell metacharacters.",
                        }

                    tf_vars.append(f"-var={key}={str_value}")

            tf_vars.append("-out=tfplan")

            # Note: use_outposts, outpost_id, use_dedicated_host, dedicated_host_id
            # are configured in terraform.tfvars and not passed via CLI

            result = subprocess.run(
                tf_vars,
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0:
                return {"success": True, "plan_output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _terraform_apply(self) -> Dict[str, Any]:
        """Apply Terraform deployment."""
        try:
            logger.info("Applying Terraform deployment...")
            result = subprocess.run(
                ["terraform", "apply", "-auto-approve", "tfplan"],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return {"success": True, "apply_output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": e.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_deployment_parameters(self, terraform_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment parameters for dry run."""
        try:
            logger.info("Validating deployment parameters...")

            cluster_name = terraform_vars.get("cluster_name", "")

            # Validate cluster name (EKS cluster names must be 1-100 characters)
            if not cluster_name or len(cluster_name) > 100:
                return {
                    "success": False,
                    "error": "Invalid cluster name: must be 1-100 characters",
                }

            # Check if Terraform directory exists
            if not os.path.exists(self.terraform_dir):
                return {
                    "success": False,
                    "error": f"Terraform directory not found: {self.terraform_dir}",
                }

            # Check if key files exist
            templates = []
            for root, dirs, files in os.walk(self.terraform_dir):
                for file in files:
                    if file.endswith((".tf", ".tfvars")):
                        templates.append(
                            os.path.relpath(os.path.join(root, file), self.terraform_dir)
                        )

            return {
                "success": True,
                "cluster_name": cluster_name,
                "region": terraform_vars.get("aws_region", "unknown"),
                "instance_type": terraform_vars.get("worker_instance_type", "unknown"),
                "node_count": terraform_vars.get("desired_capacity", 0),
                "templates": templates,
            }

        except Exception as e:
            logger.error(f"Parameter validation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def destroy_cluster(self, cluster_name: str) -> Dict[str, Any]:
        """Destroy EKS cluster using Terraform."""
        try:
            logger.info(f"Destroying EKS cluster: {cluster_name}")
            result = subprocess.run(
                ["terraform", "destroy", "-auto-approve"],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Cluster {cluster_name} destroyed successfully",
                }
            else:
                return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}
