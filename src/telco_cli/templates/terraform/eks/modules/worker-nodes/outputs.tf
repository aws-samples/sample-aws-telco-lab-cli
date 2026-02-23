output "instance_ids" {
  description = "List of worker instance IDs"
  value       = aws_instance.dedicated_worker[*].id
}

output "private_ips" {
  description = "List of worker private IP addresses"
  value       = aws_instance.dedicated_worker[*].private_ip
}
