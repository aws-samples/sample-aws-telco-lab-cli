output "prometheus_endpoint" {
  description = "Prometheus service endpoint"
  value       = "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090"
}

output "grafana_endpoint" {
  description = "Grafana service endpoint"
  value       = "http://prometheus-grafana.monitoring.svc.cluster.local"
}

# NOTE: Grafana admin password is either:
# 1. Provided via var.grafana_admin_password (recommended for production)
# 2. Auto-generated via random_password resource
# 
# To retrieve auto-generated password after deployment:
#   kubectl get secret prometheus-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d
