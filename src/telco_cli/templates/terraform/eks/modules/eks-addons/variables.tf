variable "cluster_endpoint" {
  description = "EKS cluster endpoint"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "enable_sriov_discovery" {
  description = "Enable automatic SR-IOV device discovery"
  type        = bool
  default     = true
}

variable "worker_instance_ids" {
  description = "List of worker instance IDs for SR-IOV discovery"
  type        = list(string)
  default     = []
}
