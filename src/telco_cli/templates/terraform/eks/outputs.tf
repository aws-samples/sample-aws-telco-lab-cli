# Network Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = var.deploy_vpc ? module.vpc[0].vpc_id : data.aws_vpc.existing[0].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = var.deploy_vpc ? module.vpc[0].private_subnet_ids : data.aws_subnets.existing_private[0].ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = var.deploy_vpc ? module.vpc[0].public_subnet_ids : []
}

output "edge_subnet_ids" {
  description = "Edge subnet IDs (Outposts)"
  value       = var.deploy_vpc ? module.vpc[0].edge_subnet_ids : []
}

# EKS Cluster Outputs
output "cluster_name" {
  description = "EKS cluster name"
  value       = var.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = var.deploy_eks ? module.eks[0].cluster_endpoint : data.aws_eks_cluster.existing[0].endpoint
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = var.deploy_eks ? module.eks[0].cluster_arn : data.aws_eks_cluster.existing[0].arn
}

output "cluster_version" {
  description = "EKS cluster version"
  value       = var.deploy_eks ? module.eks[0].cluster_version : data.aws_eks_cluster.existing[0].version
}

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = var.deploy_eks ? module.eks[0].cluster_security_group_id : ""
}

output "worker_security_group_id" {
  description = "Worker node security group ID"
  value       = var.deploy_eks ? module.eks[0].worker_security_group_id : ""
}

# Bastion Outputs
output "bastion_public_ip" {
  description = "Bastion host public IP"
  value       = var.deploy_bastion ? module.bastion[0].public_ip : null
}

output "bastion_instance_id" {
  description = "Bastion host instance ID"
  value       = var.deploy_bastion ? module.bastion[0].instance_id : null
}

# Observability Outputs
output "grafana_workspace_endpoint" {
  description = "Grafana workspace endpoint"
  value       = var.deploy_observability && var.install_prometheus_addons ? module.observability[0].grafana_workspace_endpoint : null
}

output "grafana_workspace_id" {
  description = "Grafana workspace ID"
  value       = var.deploy_observability && var.install_prometheus_addons ? module.observability[0].grafana_workspace_id : null
}

output "prometheus_workspace_endpoint" {
  description = "Prometheus workspace endpoint"
  value       = var.deploy_observability && var.install_prometheus_addons ? module.observability[0].prometheus_workspace_endpoint : null
}

output "prometheus_workspace_arn" {
  description = "Prometheus workspace ARN"
  value       = var.deploy_observability && var.install_prometheus_addons ? module.observability[0].prometheus_workspace_arn : null
}

# SR-IOV Observability Outputs
output "sriov_observability" {
  description = "SR-IOV observability information"
  value = var.deploy_sriov_observability && var.install_prometheus_addons ? {
    metrics_endpoint = module.sriov_observability[0].metrics_endpoint
    discovered_types = module.sriov_observability[0].discovered_instance_types
    using_discovery  = module.sriov_observability[0].using_dynamic_discovery
  } : null
}

# Utility Outputs
output "kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${var.cluster_name}"
}

output "bastion_ssh_command" {
  description = "SSH command for bastion host"
  value       = var.deploy_bastion ? "ssh -i <your-key.pem> ec2-user@${module.bastion[0].public_ip}" : null
}

# Deployment Summary
output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    cluster_name          = var.cluster_name
    cluster_version       = var.cluster_version
    vpc_deployed          = var.deploy_vpc
    eks_deployed          = var.deploy_eks
    worker_nodes_deployed = var.deploy_worker_nodes
    observability_enabled = var.deploy_observability && var.install_prometheus_addons
    sriov_observability   = var.deploy_sriov_observability && var.install_prometheus_addons
    bastion_deployed      = var.deploy_bastion
    use_outposts          = var.use_outposts
    use_dedicated_host    = var.use_dedicated_host
  }
}
