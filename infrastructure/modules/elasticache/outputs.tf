output "primary_endpoint" {
  description = "ElastiCache Redis primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "port" {
  description = "ElastiCache Redis port"
  value       = 6379
}

output "redis_url" {
  description = "Full Redis URL for application configuration"
  value       = "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:6379/0"
}
