# Prometheus using Helm
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = "monitoring"
  version    = "65.1.1"

  create_namespace = true

  values = [
    yamlencode({
      prometheus = {
        prometheusSpec = {
          serviceMonitorSelectorNilUsesHelmValues = false
          podMonitorSelectorNilUsesHelmValues     = false
          retention                               = "30d"
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = "gp3"
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = "50Gi"
                  }
                }
              }
            }
          }
        }
      }
      grafana = {
        enabled = true
        persistence = {
          enabled          = true
          storageClassName = "gp3"
          size             = "10Gi"
        }
        service = {
          type = "LoadBalancer"
        }
        adminPassword = var.grafana_admin_password != "" ? var.grafana_admin_password : random_password.grafana_admin.result
      }
      alertmanager = {
        enabled = false
      }
    })
  ]

  depends_on = [var.cluster_endpoint]
}

# ServiceMonitor for SR-IOV metrics
resource "kubernetes_manifest" "sriov_service_monitor" {
  count = var.enable_sriov_monitoring ? 1 : 0

  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    metadata = {
      name      = "sriov-network-metrics"
      namespace = "monitoring"
      labels = {
        app = "sriov-network-metrics-exporter"
      }
    }
    spec = {
      selector = {
        matchLabels = {
          app = "sriov-network-metrics-exporter"
        }
      }
      namespaceSelector = {
        matchNames = ["kube-system"]
      }
      endpoints = [{
        port     = "metrics"
        interval = "30s"
        path     = "/metrics"
      }]
    }
  }

  depends_on = [helm_release.prometheus]
}
