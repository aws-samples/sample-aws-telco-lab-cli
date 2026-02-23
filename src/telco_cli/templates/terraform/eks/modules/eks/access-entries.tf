# EKS Access Entries - Manually configured
# resource "aws_eks_access_entry" "worker" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = aws_iam_role.worker.arn
#   type          = "EC2_LINUX"

#   tags = var.tags
# }

# data "aws_caller_identity" "current" {}

# resource "aws_eks_access_entry" "account" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
#   type          = "STANDARD"

#   tags = var.tags
# }

# resource "aws_eks_access_policy_association" "account_cluster_admin" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = aws_eks_access_entry.account.principal_arn
#   policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

#   access_scope {
#     type = "cluster"
#   }
# }

# resource "aws_eks_access_policy_association" "account_admin" {
#   cluster_name  = aws_eks_cluster.main.name
#   principal_arn = aws_eks_access_entry.account.principal_arn
#   policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy"

#   access_scope {
#     type = "cluster"
#   }
# }
