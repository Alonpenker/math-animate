variable "name_prefix" {
  description = "Prefix applied to all resource names"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_api_sg_id" {
  description = "Security group ID for ECS API tasks"
  type        = string
}

variable "target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

variable "ecs_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role (runtime permissions)"
  type        = string
}

variable "image_uri" {
  description = "Full Docker Hub image URI for the backend (e.g. youruser/math-animate-backend:abc1234)"
  type        = string
}

variable "cpu" {
  description = "Task CPU units"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Task memory in MiB"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 1
}

variable "sqs_queue_url" {
  description = "SQS job queue URL injected as environment variable"
  type        = string
}

variable "artifact_bucket_name" {
  description = "Artifact S3 bucket name"
  type        = string
}

variable "database_url" {
  description = "PostgreSQL connection string"
  type        = string
  sensitive   = true
}

variable "redis_url" {
  description = "Redis connection URL"
  type        = string
}

variable "frontend_url" {
  description = "Frontend URL for CORS configuration"
  type        = string
}

variable "dockerhub_credentials_secret_arn" {
  description = "Secrets Manager ARN for Docker Hub credentials (JSON with username and password)"
  type        = string
}
