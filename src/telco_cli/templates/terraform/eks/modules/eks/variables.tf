variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "cluster_version" {
  description = "EKS cluster version"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for EKS cluster"
  type        = list(string)
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

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
}

variable "public_access_cidrs" {
  description = <<-EOT
    SECURITY: List of CIDR blocks allowed to access the EKS public API endpoint.

    WARNING: Default ["0.0.0.0/0"] allows access from any IP and is intended
    for LAB/DEMO environments only.
    PRODUCTION: Change to your organization's IP ranges (e.g., ["10.0.0.0/8"]).
  EOT
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "secrets_encryption_kms_key_arn" {
  description = <<-EOT
    ARN of the KMS key to encrypt Kubernetes secrets at rest.
    Leave empty ("") to skip secrets encryption.
    RECOMMENDED: Provide a KMS key ARN for production deployments.
  EOT
  type        = string
  default     = ""
}
