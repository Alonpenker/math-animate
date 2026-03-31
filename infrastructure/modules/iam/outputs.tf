output "ecs_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role (runtime permissions)"
  value       = aws_iam_role.ecs_task.arn
}

output "ec2_worker_role_arn" {
  description = "ARN of the EC2 worker IAM role"
  value       = aws_iam_role.ec2_worker.arn
}

output "ec2_worker_instance_profile_name" {
  description = "Name of the EC2 worker instance profile"
  value       = aws_iam_instance_profile.ec2_worker.name
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions OIDC deploy role"
  value       = aws_iam_role.github_actions.arn
}

output "storage_access_key_id" {
  description = "Access key ID for the storage IAM user (MinIO SDK)"
  value       = aws_iam_access_key.storage.id
}

output "storage_secret_access_key" {
  description = "Secret access key for the storage IAM user (MinIO SDK)"
  value       = aws_iam_access_key.storage.secret
  sensitive   = true
}
