# ── Networking ───────────────────────────────────────────────────────────────
output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs (ECS, EC2, RDS, ElastiCache)"
  value       = module.networking.private_subnet_ids
}

# ── ALB ──────────────────────────────────────────────────────────────────────
output "alb_dns_name" {
  description = "ALB DNS name — use this as the API base URL"
  value       = module.alb.alb_dns_name
}

# ── ECS ──────────────────────────────────────────────────────────────────────
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS API service name"
  value       = module.ecs.service_name
}

# ── EC2 Worker ───────────────────────────────────────────────────────────────
output "ec2_worker_instance_id" {
  description = "EC2 worker instance ID (used by GitHub Actions SSM command)"
  value       = module.ec2_worker.instance_id
}

output "ec2_worker_private_ip" {
  description = "EC2 worker private IP"
  value       = module.ec2_worker.private_ip
}

# ── RDS ──────────────────────────────────────────────────────────────────────
output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)"
  value       = module.rds.endpoint
}

output "rds_db_name" {
  description = "RDS database name"
  value       = module.rds.db_name
}

output "db_password_secret_arn" {
  description = "Secrets Manager ARN for the RDS master password"
  value       = module.rds.db_password_secret_arn
}

# ── ElastiCache ───────────────────────────────────────────────────────────────
output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = module.elasticache.primary_endpoint
}

# ── SQS ──────────────────────────────────────────────────────────────────────
output "sqs_queue_url" {
  description = "SQS main queue URL"
  value       = module.sqs.queue_url
}

output "sqs_dlq_url" {
  description = "SQS DLQ URL"
  value       = module.sqs.dlq_url
}

# ── S3 ───────────────────────────────────────────────────────────────────────
output "s3_artifact_bucket" {
  description = "Artifact S3 bucket name"
  value       = module.s3.artifact_bucket_name
}

output "s3_frontend_bucket" {
  description = "Frontend S3 bucket name"
  value       = module.s3.frontend_bucket_name
}

