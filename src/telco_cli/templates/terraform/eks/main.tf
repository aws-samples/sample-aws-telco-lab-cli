terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

provider "kubernetes" {
  host                   = var.deploy_eks ? module.eks[0].cluster_endpoint : data.aws_eks_cluster.existing[0].endpoint
  cluster_ca_certificate = base64decode(var.deploy_eks ? module.eks[0].cluster_ca_certificate : data.aws_eks_cluster.existing[0].certificate_authority[0].data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", var.cluster_name, "--profile", var.aws_profile]
  }
}

provider "helm" {
  kubernetes {
    host                   = var.deploy_eks ? module.eks[0].cluster_endpoint : data.aws_eks_cluster.existing[0].endpoint
    cluster_ca_certificate = base64decode(var.deploy_eks ? module.eks[0].cluster_ca_certificate : data.aws_eks_cluster.existing[0].certificate_authority[0].data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = [
        "eks",
        "get-token",
        "--cluster-name",
        var.cluster_name,
        "--region",
        var.aws_region,
        "--profile",
        var.aws_profile
      ]
    }
  }
}

# Data sources for existing resources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Auto-discover key pair if not specified
data "aws_key_pair" "worker" {
  count              = var.worker_node_key_pair_name == null && var.existing_key_pair_name == "" ? 1 : 0
  key_name           = "cse-dev-key-${data.aws_region.current.name}"
  include_public_key = false
}

# Use existing key pair if specified
data "aws_key_pair" "existing" {
  count    = var.existing_key_pair_name != "" ? 1 : 0
  key_name = var.existing_key_pair_name
}

locals {
  key_pair_name = var.existing_key_pair_name != "" ? var.existing_key_pair_name : (
    var.worker_node_key_pair_name != null ? var.worker_node_key_pair_name : (
      length(data.aws_key_pair.worker) > 0 ? data.aws_key_pair.worker[0].key_name : null
    )
  )
}

data "aws_region" "current" {}

# VPC Module - Conditional deployment
module "vpc" {
  count  = var.deploy_vpc ? 1 : 0
  source = "./modules/vpc"

  vpc_cidr           = var.vpc_cidr
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 3)
  edge_subnet_cidr   = var.edge_subnet_cidr
  use_outposts       = var.use_outposts
  outpost_id         = var.outpost_id
  outpost_account_id = var.outpost_account_id

  tags = local.common_tags
}

# EKS Module - Conditional deployment
module "eks" {
  count  = var.deploy_eks ? 1 : 0
  source = "./modules/eks"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  vpc_id          = var.deploy_vpc ? module.vpc[0].vpc_id : data.aws_vpc.existing[0].id
  subnet_ids      = var.deploy_vpc ? module.vpc[0].private_subnet_ids : data.aws_subnets.existing_private[0].ids

  install_observability_addons = var.install_observability_addons
  install_prometheus_addons    = var.install_prometheus_addons
  use_cilium                   = var.use_cilium

  tags = local.common_tags
}

# Worker Nodes Module - Conditional deployment
module "worker_nodes" {
  count  = var.deploy_worker_nodes ? 1 : 0
  source = "./modules/worker-nodes"

  cluster_name           = var.cluster_name
  cluster_version        = var.cluster_version
  cluster_endpoint       = var.deploy_eks ? module.eks[0].cluster_endpoint : data.aws_eks_cluster.existing[0].endpoint
  cluster_ca_certificate = var.deploy_eks ? module.eks[0].cluster_ca_certificate : data.aws_eks_cluster.existing[0].certificate_authority[0].data
  worker_role_name       = var.deploy_eks ? module.eks[0].worker_role_name : "${var.cluster_name}-worker-role"

  vpc_id                = var.deploy_vpc ? module.vpc[0].vpc_id : data.aws_vpc.existing[0].id
  subnet_ids            = var.use_outposts && var.use_dedicated_host ? (var.deploy_vpc ? module.vpc[0].edge_subnet_ids : []) : (var.deploy_vpc ? module.vpc[0].private_subnet_ids : data.aws_subnets.existing_private[0].ids)
  worker_security_group = var.deploy_eks ? module.eks[0].worker_security_group_id : ""

  # Dedicated Host Configuration
  use_dedicated_host = var.use_dedicated_host
  dedicated_host_id  = var.dedicated_host_id

  # Instance Configuration
  instance_type    = var.use_outposts ? var.outpost_instance_type : var.worker_instance_type
  key_pair_name    = var.worker_node_key_pair_name
  volume_size      = var.worker_node_volume_size
  desired_capacity = var.desired_capacity

  tags = local.common_tags
}

# Observability Module - Conditional deployment (Helm-based)
module "observability" {
  count  = var.deploy_observability && var.install_prometheus_addons ? 1 : 0
  source = "./modules/observability"

  cluster_name            = var.cluster_name
  cluster_endpoint        = var.deploy_eks ? module.eks[0].cluster_endpoint : data.aws_eks_cluster.existing[0].endpoint
  enable_sriov_monitoring = var.deploy_sriov_observability
  grafana_admin_password  = var.grafana_admin_password

  tags = local.common_tags
}

# SR-IOV Observability Module - Conditional deployment (Helm-based)
module "sriov_observability" {
  count  = var.deploy_sriov_observability && var.install_prometheus_addons ? 1 : 0
  source = "./modules/sriov-observability"

  cluster_name                = var.cluster_name
  enable_dynamic_discovery    = false
  telco_instance_type         = var.use_outposts ? var.outpost_instance_type : var.worker_instance_type
  cluster_ready               = var.deploy_eks ? module.eks[0].cluster_endpoint : data.aws_eks_cluster.existing[0].endpoint
  nodes_ready                 = var.deploy_worker_nodes ? module.worker_nodes[0].instance_ids : []
  prometheus_operator_enabled = true

  depends_on = [
    data.aws_eks_cluster.existing,
    module.observability
  ]
}

# Bastion Host Module - Conditional deployment
module "bastion" {
  count  = var.deploy_bastion ? 1 : 0
  source = "./modules/bastion"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  aws_region      = var.aws_region
  vpc_id          = var.deploy_vpc ? module.vpc[0].vpc_id : data.aws_vpc.existing[0].id
  subnet_id       = var.deploy_vpc ? module.vpc[0].public_subnet_ids[0] : ""
  key_pair_name   = var.worker_node_key_pair_name

  tags = local.common_tags
}

# EKS Addons Module - Conditional deployment
module "eks_addons" {
  count  = var.deploy_eks_addons ? 1 : 0
  source = "./modules/eks-addons"

  cluster_endpoint       = data.aws_eks_cluster.existing[0].endpoint
  worker_instance_ids    = var.deploy_worker_nodes ? module.worker_nodes[0].instance_ids : []
  enable_sriov_discovery = true # Enable auto-discovery with real instance IDs
  tags                   = local.common_tags

  depends_on = [
    data.aws_eks_cluster.existing,
    module.worker_nodes
  ]
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = "sjc38-eks"
    ManagedBy   = "terraform"
  }
}
