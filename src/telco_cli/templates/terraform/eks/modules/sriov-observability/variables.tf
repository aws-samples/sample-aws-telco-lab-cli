variable "cluster_name" {
  description = "EKS cluster name for dynamic instance discovery"
  type        = string
}

variable "telco_instance_type" {
  description = "Fallback instance type for telco nodes with SR-IOV capability"
  type        = string
  default     = "bmn-sf2.metal-32xl"
}

variable "enable_dynamic_discovery" {
  description = "Enable dynamic discovery of telco instance types"
  type        = bool
  default     = true
}

variable "cluster_ready" {
  description = "Dependency to ensure cluster is ready before deployment"
  type        = any
  default     = null
}

variable "nodes_ready" {
  description = "Dependency to ensure worker nodes are ready before discovery"
  type        = any
  default     = null
}

variable "prometheus_operator_enabled" {
  description = "Whether Prometheus Operator is installed for ServiceMonitor"
  type        = bool
  default     = false
}
