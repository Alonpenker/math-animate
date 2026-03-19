output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "service_name" {
  description = "ECS API service name"
  value       = aws_ecs_service.api.name
}

output "task_definition_arn" {
  description = "Latest ECS task definition ARN"
  value       = aws_ecs_task_definition.api.arn
}

