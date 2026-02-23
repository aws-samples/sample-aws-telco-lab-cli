output "instance_id" {
  description = "Bastion host instance ID"
  value       = aws_instance.bastion.id
}

output "public_ip" {
  description = "Bastion host public IP"
  value       = aws_instance.bastion.public_ip
}

output "security_group_id" {
  description = "Bastion security group ID"
  value       = aws_security_group.bastion.id
}
