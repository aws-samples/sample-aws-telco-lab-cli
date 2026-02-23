variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "cluster_version" {
  description = "EKS cluster version"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_id" {
  description = "Public subnet ID for bastion"
  type        = string
}

variable "key_pair_name" {
  description = "Key pair name for bastion access"
  type        = string
}

variable "instance_type" {
  description = "Instance type for bastion host"
  type        = string
  default     = "t3.medium"
}

variable "volume_size" {
  description = "EBS volume size for bastion host"
  type        = number
  default     = 20
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
}

variable "allowed_ssh_cidr_blocks" {
  description = <<-EOT
    SECURITY CRITICAL: List of CIDR blocks allowed to SSH to the bastion host.
    
    WARNING: The default value ["0.0.0.0/0"] opens SSH access to the entire internet.
    This is a significant security risk and should ONLY be used for testing/development.
    
    PRODUCTION REQUIREMENT: You MUST change this to your organization's IP ranges.
    
    RECOMMENDED: Restrict to your organization's IP ranges or VPN endpoints.
    Example: ["203.0.113.0/24", "198.51.100.0/24"]
    
    To find your current IP: curl ifconfig.me
  EOT
  type        = list(string)
  default     = ["0.0.0.0/0"] # TESTING ONLY - Change for production use

  validation {
    condition = alltrue([
      for cidr in var.allowed_ssh_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All elements must be valid CIDR blocks (e.g., '10.0.0.0/8')."
  }
}
