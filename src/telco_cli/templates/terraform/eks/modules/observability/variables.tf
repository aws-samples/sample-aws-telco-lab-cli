variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "cluster_endpoint" {
  description = "EKS cluster endpoint"
  type        = string
}

variable "enable_sriov_monitoring" {
  description = "Enable SR-IOV network metrics monitoring"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  default     = ""
  sensitive   = true
}
