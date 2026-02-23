# Cilium CNI Installation (when use_cilium = true)
resource "helm_release" "cilium" {
  count = var.use_cilium ? 1 : 0

  name       = "cilium"
  repository = "https://helm.cilium.io/"
  chart      = "cilium"
  version    = "1.17.6"
  namespace  = "kube-system"

  # Wait for Cilium to be fully ready before considering deployment complete
  wait          = true
  wait_for_jobs = true
  timeout       = 600 # 10 minutes timeout

  # Use working upstream images (AWS ECR operator image is broken)
  set {
    name  = "image.repository"
    value = "quay.io/cilium/cilium"
  }

  set {
    name  = "image.tag"
    value = "v1.17.6"
  }

  set {
    name  = "operator.image.repository"
    value = "quay.io/cilium/operator-aws"
  }

  set {
    name  = "operator.image.tag"
    value = "v1.17.6"
  }

  # EKS-compatible Cilium configuration
  set {
    name  = "eni.enabled"
    value = "true"
  }

  set {
    name  = "ipam.mode"
    value = "eni"
  }

  set {
    name  = "egressMasqueradeInterfaces"
    value = "eth0"
  }

  set {
    name  = "routingMode"
    value = "native"
  }

  set {
    name  = "kubeProxyReplacement"
    value = "true"
  }

  depends_on = [aws_eks_cluster.main]
}

# Wait for Cilium to be ready before removing VPC-CNI
resource "time_sleep" "wait_for_cilium" {
  count = var.use_cilium ? 1 : 0

  create_duration = "60s" # Additional safety buffer

  depends_on = [helm_release.cilium]
}
