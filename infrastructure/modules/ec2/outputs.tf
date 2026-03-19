output "instance_id" {
  description = "EC2 worker instance ID"
  value       = aws_instance.worker.id
}

output "private_ip" {
  description = "EC2 worker private IP address"
  value       = aws_instance.worker.private_ip
}
