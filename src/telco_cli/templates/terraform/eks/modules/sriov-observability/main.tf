# Dynamic SR-IOV hardware discovery - waits for cluster to be ready
data "aws_instances" "telco_workers" {
  count = var.enable_dynamic_discovery ? 1 : 0

  filter {
    name   = "tag:kubernetes.io/cluster/${var.cluster_name}"
    values = ["owned"]
  }

  filter {
    name   = "instance-state-name"
    values = ["running"]
  }

  # Ensure this runs after cluster and nodes are ready
  depends_on = [var.cluster_ready, var.nodes_ready]
}

# Get instance types dynamically
data "aws_instance" "telco_worker_details" {
  count = var.enable_dynamic_discovery ? length(data.aws_instances.telco_workers[0].ids) : 0

  instance_id = data.aws_instances.telco_workers[0].ids[count.index]
}

# Determine telco instance types dynamically
locals {
  discovered_instance_types = var.enable_dynamic_discovery ? distinct([
    for instance in data.aws_instance.telco_worker_details : instance.instance_type
    if can(regex("^(bmn-|m7i\\..*metal|c7i\\..*metal)", instance.instance_type))
  ]) : []

  # Use discovered types or fallback to variable
  target_instance_types = length(local.discovered_instance_types) > 0 ? local.discovered_instance_types : [var.telco_instance_type]

  # Create node selector for all discovered telco instance types
  node_selector = length(local.target_instance_types) == 1 ? {
    "node.kubernetes.io/instance-type" = local.target_instance_types[0]
  } : {}

  # Use node affinity for multiple instance types
  use_node_affinity = length(local.target_instance_types) > 1
}

resource "kubernetes_daemon_set_v1" "sriov_metrics_exporter" {
  metadata {
    name      = "sriov-metrics-exporter"
    namespace = "kube-system"
    labels = {
      app = "sriov-metrics-exporter"
    }
  }

  spec {
    selector {
      match_labels = {
        app = "sriov-metrics-exporter"
      }
    }

    template {
      metadata {
        labels = {
          app = "sriov-metrics-exporter"
        }
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "9101"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        host_network = true
        host_pid     = true

        # Dynamic node selection
        node_selector = local.use_node_affinity ? {} : local.node_selector

        # Use affinity for multiple instance types
        dynamic "affinity" {
          for_each = local.use_node_affinity ? [1] : []
          content {
            node_affinity {
              required_during_scheduling_ignored_during_execution {
                node_selector_term {
                  match_expressions {
                    key      = "node.kubernetes.io/instance-type"
                    operator = "In"
                    values   = local.target_instance_types
                  }
                }
              }
            }
          }
        }

        toleration {
          operator = "Exists"
        }

        container {
          name  = "sriov-exporter"
          image = "prom/node-exporter:latest"
          args = [
            "--path.procfs=/host/proc",
            "--path.sysfs=/host/sys",
            "--collector.netclass",
            "--collector.netdev",
            "--collector.netstat",
            "--collector.infiniband",
            "--web.listen-address=0.0.0.0:9101"
          ]

          port {
            container_port = 9101
            name           = "metrics"
          }

          resources {
            requests = {
              memory = "64Mi"
              cpu    = "50m"
            }
            limits = {
              memory = "128Mi"
              cpu    = "100m"
            }
          }

          volume_mount {
            name       = "proc"
            mount_path = "/host/proc"
            read_only  = true
          }

          volume_mount {
            name       = "sys"
            mount_path = "/host/sys"
            read_only  = true
          }

          volume_mount {
            name       = "sriov-config"
            mount_path = "/host/sys/class/net"
            read_only  = true
          }
        }

        container {
          name    = "sriov-vf-exporter"
          image   = "busybox:latest"
          command = ["/bin/sh"]
          args = [
            "-c",
            <<-EOT
            while true; do
              echo "# HELP sriov_vf_count Number of SR-IOV VFs configured"
              echo "# TYPE sriov_vf_count gauge"
              echo "# HELP sriov_vf_total Maximum SR-IOV VFs supported"  
              echo "# TYPE sriov_vf_total gauge"
              echo "# HELP sriov_interface_info SR-IOV interface information"
              echo "# TYPE sriov_interface_info gauge"
              for dev in /host/sys/class/net/*/device/sriov_numvfs; do
                if [ -f "$dev" ]; then
                  iface=$(basename $(dirname $(dirname $dev)))
                  vfs=$(cat $dev 2>/dev/null || echo 0)
                  total=$(cat $(dirname $dev)/sriov_totalvfs 2>/dev/null || echo 0)
                  vendor=$(cat $(dirname $dev)/vendor 2>/dev/null | sed 's/0x//' || echo "unknown")
                  device=$(cat $(dirname $dev)/device 2>/dev/null | sed 's/0x//' || echo "unknown")
                  echo "sriov_vf_count{interface=\"$iface\",vendor=\"$vendor\",device=\"$device\"} $vfs"
                  echo "sriov_vf_total{interface=\"$iface\",vendor=\"$vendor\",device=\"$device\"} $total"
                  echo "sriov_interface_info{interface=\"$iface\",vendor=\"$vendor\",device=\"$device\"} 1"
                fi
              done > /tmp/sriov_metrics.prom
              sleep 30
            done
            EOT
          ]

          volume_mount {
            name       = "sys"
            mount_path = "/host/sys"
            read_only  = true
          }

          volume_mount {
            name       = "metrics-volume"
            mount_path = "/tmp"
          }
        }

        volume {
          name = "proc"
          host_path {
            path = "/proc"
          }
        }

        volume {
          name = "sys"
          host_path {
            path = "/sys"
          }
        }

        volume {
          name = "sriov-config"
          host_path {
            path = "/sys/class/net"
          }
        }

        volume {
          name = "metrics-volume"
          empty_dir {}
        }
      }
    }
  }

  depends_on = [var.cluster_ready]
}

resource "kubernetes_service_v1" "sriov_metrics_exporter" {
  metadata {
    name      = "sriov-metrics-exporter"
    namespace = "kube-system"
    labels = {
      app = "sriov-metrics-exporter"
    }
    annotations = {
      "prometheus.io/scrape" = "true"
      "prometheus.io/port"   = "9101"
    }
  }

  spec {
    selector = {
      app = "sriov-metrics-exporter"
    }

    port {
      port        = 9101
      target_port = 9101
      name        = "metrics"
    }
  }
}

resource "kubernetes_manifest" "sriov_service_monitor" {
  count = var.prometheus_operator_enabled ? 1 : 0

  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    metadata = {
      name      = "sriov-metrics-exporter"
      namespace = "kube-system"
      labels = {
        app = "sriov-metrics-exporter"
      }
    }
    spec = {
      selector = {
        matchLabels = {
          app = "sriov-metrics-exporter"
        }
      }
      endpoints = [{
        port     = "metrics"
        interval = "30s"
        path     = "/metrics"
      }]
    }
  }

  depends_on = [kubernetes_service_v1.sriov_metrics_exporter]
}
