variable "name_prefix" {
  description = "Prefix applied to all resource names"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance (Amazon Linux 2023)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "private_subnet_ids" {
  description = "Private subnet IDs — worker is placed in the first one"
  type        = list(string)
}

variable "worker_sg_id" {
  description = "Security group ID for the EC2 worker"
  type        = string
}

variable "instance_profile_name" {
  description = "IAM instance profile name for the worker"
  type        = string
}

variable "image_uri" {
  description = "Full Docker Hub image URI for the backend container (e.g. youruser/math-animate-backend:abc1234)"
  type        = string
}

variable "artifact_bucket_name" {
  description = "Artifact S3 bucket name"
  type        = string
}

variable "sqs_queue_url" {
  description = "SQS job queue URL"
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

variable "docker_compose_content" {
  description = "Content of the EC2 docker-compose.yml to be injected into the userdata template"
  type        = string
}

