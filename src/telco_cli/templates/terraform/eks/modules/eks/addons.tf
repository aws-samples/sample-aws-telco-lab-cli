# Essential EKS Add-ons
resource "aws_eks_addon" "coredns" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "coredns"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_cluster.main]
  tags       = var.tags
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "kube-proxy"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_cluster.main]
  tags       = var.tags
}

resource "aws_eks_addon" "vpc_cni" {
  count = var.use_cilium ? 0 : 1

  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "vpc-cni"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_cluster.main]
  tags       = var.tags
}

# Note: When use_cilium = true, VPC-CNI addon is not created
# Cilium is installed via Helm and waits for readiness before proceeding

resource "aws_eks_addon" "ebs_csi" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "aws-ebs-csi-driver"
  service_account_role_arn    = aws_iam_role.ebs_csi.arn
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_cluster.main]
  tags       = var.tags
}

# Pod Identity Agent for modern authentication
resource "aws_eks_addon" "pod_identity" {
  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "eks-pod-identity-agent"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_cluster.main]
  tags       = var.tags
}

# Observability Add-ons (conditional)
resource "aws_eks_addon" "cloudwatch_observability" {
  count = var.install_observability_addons ? 1 : 0

  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "amazon-cloudwatch-observability"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_cluster.main]
  tags       = var.tags
}

# Amazon EKS Distro for Prometheus (conditional)
resource "aws_eks_addon" "adot" {
  count = var.install_prometheus_addons ? 1 : 0

  cluster_name                = aws_eks_cluster.main.name
  addon_name                  = "adot"
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_cluster.main]
  tags       = var.tags
}
