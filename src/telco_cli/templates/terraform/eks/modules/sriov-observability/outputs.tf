output "service_name" {
  description = "Name of the SR-IOV metrics service"
  value       = kubernetes_service_v1.sriov_metrics_exporter.metadata[0].name
}

output "service_namespace" {
  description = "Namespace of the SR-IOV metrics service"
  value       = kubernetes_service_v1.sriov_metrics_exporter.metadata[0].namespace
}

output "metrics_endpoint" {
  description = "Metrics endpoint for Prometheus scraping"
  value       = "${kubernetes_service_v1.sriov_metrics_exporter.metadata[0].name}.${kubernetes_service_v1.sriov_metrics_exporter.metadata[0].namespace}:9100/metrics"
}

output "discovered_instance_types" {
  description = "Dynamically discovered telco instance types"
  value       = local.target_instance_types
}

output "using_dynamic_discovery" {
  description = "Whether dynamic discovery was used"
  value       = var.enable_dynamic_discovery && length(local.discovered_instance_types) > 0
}
