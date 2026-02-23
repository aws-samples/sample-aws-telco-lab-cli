variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use"
  type        = string
  default     = "default"
}

variable "existing_vpc_id" {
  description = "Existing VPC ID when deploy_vpc=false"
  type        = string
  default     = ""
}

variable "existing_key_pair_name" {
  description = "Existing key pair name (overrides auto-discovery)"
  type        = string
  default     = ""
}

variable "grafana_admin_password" {
  description = "Grafana admin password (generates random if empty)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "test"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "sjc38-eks-cluster"
}

variable "cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.32"

  validation {
    condition     = can(regex("^1\\.(2[8-9]|3[0-9])$", var.cluster_version))
    error_message = "EKS cluster version must be 1.28 or higher."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "100.77.0.0/16"
}

variable "edge_subnet_cidr" {
  description = "CIDR block for edge subnet"
  type        = string
  default     = "100.77.4.0/24"
}

variable "use_outposts" {
  description = "Deploy on AWS Outposts"
  type        = bool
  default     = false
}

variable "outpost_id" {
  description = "Outpost ID for deployment"
  type        = string
  default     = ""

  validation {
    condition     = var.outpost_id == "" || can(regex("^op-[a-f0-9]{17}$", var.outpost_id))
    error_message = "Outpost ID must be in format 'op-' followed by 17 hexadecimal characters."
  }
}

variable "outpost_account_id" {
  description = "Account ID for Outpost ARN (required when use_outposts=true for RAM shared Outposts)"
  type        = string
  default     = ""
}

variable "use_dedicated_host" {
  description = "Use dedicated host for worker nodes"
  type        = bool
  default     = false
}

variable "dedicated_host_id" {
  description = "Dedicated host ID"
  type        = string
  default     = ""

  validation {
    condition     = var.dedicated_host_id == "" || can(regex("^h-[a-f0-9]{17}$", var.dedicated_host_id))
    error_message = "Dedicated host ID must be in format 'h-' followed by 17 hexadecimal characters."
  }
}

variable "worker_instance_type" {
  description = "Instance type for region worker nodes"
  type        = string
  default     = "m5.2xlarge"
}

variable "outpost_instance_type" {
  description = "Instance type for Outpost worker nodes"
  type        = string
  default     = "bmn-sf2.metal-32xl"
}

variable "worker_node_key_pair_name" {
  description = "Key pair name for worker nodes"
  type        = string
  default     = null
}

variable "worker_node_volume_size" {
  description = "EBS volume size for worker nodes"
  type        = number
  default     = 100
}

variable "desired_capacity" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 1
}

variable "install_observability_addons" {
  description = "Install CloudWatch observability add-ons"
  type        = bool
  default     = true
}

variable "install_prometheus_addons" {
  description = "Install Prometheus monitoring add-ons"
  type        = bool
  default     = true
}

variable "use_cilium" {
  description = "Use Cilium CNI instead of VPC CNI"
  type        = bool
  default     = false
}
