# Generate random password for Grafana if not provided
resource "random_password" "grafana_admin" {
  length  = 16
  special = true
}