variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "edge_subnet_cidr" {
  description = "CIDR block for edge subnet"
  type        = string
}

variable "use_outposts" {
  description = "Deploy on AWS Outposts"
  type        = bool
}

variable "outpost_id" {
  description = "Outpost ID"
  type        = string
}

variable "outpost_account_id" {
  description = "Account ID for Outpost ARN (for RAM shared Outposts)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
}
