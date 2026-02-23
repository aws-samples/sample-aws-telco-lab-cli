# Deployment Control Variables for Selective Module Management
# These variables allow you to control which components are deployed/managed by terraform

variable "deploy_vpc" {
  description = "Deploy and manage VPC infrastructure via terraform"
  type        = bool
  default     = false # Set to false to use existing VPC
}

variable "deploy_eks" {
  description = "Deploy and manage EKS cluster via terraform"
  type        = bool
  default     = false # Set to false to use existing EKS cluster
}

variable "deploy_worker_nodes" {
  description = "Deploy and manage worker nodes via terraform"
  type        = bool
  default     = false # Set to false to use existing worker nodes
}

variable "deploy_observability" {
  description = "Deploy observability stack (Prometheus/Grafana)"
  type        = bool
  default     = true # Enable observability deployment
}

variable "deploy_sriov_observability" {
  description = "Deploy SR-IOV specific observability components"
  type        = bool
  default     = true # Enable SR-IOV observability
}

variable "deploy_bastion" {
  description = "Deploy bastion host"
  type        = bool
  default     = false # Set to false to skip bastion deployment
}

variable "deploy_eks_addons" {
  description = "Deploy EKS addons (Outposts bundle)"
  type        = bool
  default     = false # Set to false to skip addons deployment
}

# Data sources for existing infrastructure when not deploying via terraform
data "aws_vpc" "existing" {
  count = var.deploy_vpc ? 0 : 1

  # Use provided VPC ID or fallback to default VPC
  id = var.existing_vpc_id != "" ? var.existing_vpc_id : data.aws_vpcs.default[0].ids[0]
}

# Fallback to default VPC if no VPC ID provided
data "aws_vpcs" "default" {
  count = var.deploy_vpc || var.existing_vpc_id != "" ? 0 : 1

  filter {
    name   = "is-default"
    values = ["true"]
  }
}

data "aws_subnets" "existing_private" {
  count = var.deploy_vpc ? 0 : 1

  # Auto-detect subnets from EKS cluster
  filter {
    name   = "subnet-id"
    values = data.aws_eks_cluster.existing[0].vpc_config[0].subnet_ids
  }
}

data "aws_eks_cluster" "existing" {
  count = var.deploy_eks ? 0 : 1
  name  = var.cluster_name
}

data "aws_eks_cluster_auth" "existing" {
  count = var.deploy_eks ? 0 : 1
  name  = var.cluster_name
}
