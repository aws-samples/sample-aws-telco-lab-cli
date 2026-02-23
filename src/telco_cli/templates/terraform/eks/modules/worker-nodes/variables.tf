variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "cluster_version" {
  description = "EKS cluster version"
  type        = string
}

variable "worker_role_name" {
  description = "Worker node IAM role name"
  type        = string
}

variable "cluster_endpoint" {
  description = "EKS cluster endpoint"
  type        = string
}

variable "cluster_ca_certificate" {
  description = "EKS cluster CA certificate"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for worker nodes"
  type        = list(string)
}

variable "worker_security_group" {
  description = "Security group ID for worker nodes"
  type        = string
}

variable "use_dedicated_host" {
  description = "Use dedicated host for worker nodes"
  type        = bool
}

variable "dedicated_host_id" {
  description = "Dedicated host ID"
  type        = string
}

variable "instance_type" {
  description = "Instance type for worker nodes"
  type        = string
}

variable "key_pair_name" {
  description = "Key pair name for worker nodes"
  type        = string
}

variable "volume_size" {
  description = "EBS volume size for worker nodes"
  type        = number
}

variable "desired_capacity" {
  description = "Desired number of worker nodes"
  type        = number
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
}
