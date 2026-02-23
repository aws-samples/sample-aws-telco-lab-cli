# Data validation for existing resources
# Validates that specified resources exist before deployment

# Validate existing key pair if specified
data "aws_key_pair" "validate_existing" {
  count    = var.existing_key_pair_name != "" ? 1 : 0
  key_name = var.existing_key_pair_name
}

# Validate worker node key pair if specified
data "aws_key_pair" "validate_worker" {
  count    = var.worker_node_key_pair_name != null ? 1 : 0
  key_name = var.worker_node_key_pair_name
}

# Validate existing VPC if specified
data "aws_vpc" "validate_existing_vpc" {
  count = !var.deploy_vpc && var.existing_vpc_id != "" ? 1 : 0
  id    = var.existing_vpc_id
}

# Validate existing EKS cluster if not deploying
data "aws_eks_cluster" "validate_existing_cluster" {
  count = !var.deploy_eks ? 1 : 0
  name  = var.cluster_name
}