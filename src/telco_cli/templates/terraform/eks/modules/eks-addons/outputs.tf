output "release_name" {
  description = "Helm release name"
  value       = helm_release.outposts_bundle.name
}

output "release_status" {
  description = "Helm release status"
  value       = helm_release.outposts_bundle.status
}
