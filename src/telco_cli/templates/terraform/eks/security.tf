# Security best practices and improvements

# Restrict worker node security group ingress
resource "aws_security_group_rule" "worker_cluster_ingress_restricted" {
  type                     = "ingress"
  from_port                = 1025
  to_port                  = 65535
  protocol                 = "tcp"
  source_security_group_id = var.deploy_eks ? module.eks[0].cluster_security_group_id : ""
  security_group_id        = var.deploy_eks ? module.eks[0].worker_security_group_id : ""
  description              = "Allow cluster to worker nodes on unprivileged ports"

  count = var.deploy_eks ? 1 : 0
}

# Secure defaults for storage
locals {
  storage_class = "gp3"
  encrypt_ebs   = true
}