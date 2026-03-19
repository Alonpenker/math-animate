variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-north-1"
}

variable "environment" {
  description = "Deployment environment name (prod, staging, etc.)"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use (must have at least 2)"
  type        = list(string)
  default     = ["eu-north-1a", "eu-north-1b"]
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "mathanimate"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "mathanimate"
}

variable "cache_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "worker_instance_type" {
  description = "EC2 instance type for the Celery worker"
  type        = string
  default     = "t3.medium"
}

variable "worker_ami_id" {
  description = "AMI ID for the EC2 worker instance (Amazon Linux 2023)"
  type        = string
}

variable "api_cpu" {
  description = "ECS task CPU units for the API (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "ECS task memory in MiB for the API"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of ECS API tasks"
  type        = number
  default     = 1
}

variable "alb_certificate_arn" {
  description = "ACM certificate ARN for the ALB HTTPS listener. Leave empty to use HTTP only."
  type        = string
  default     = ""
}

variable "frontend_url" {
  description = "Frontend URL passed to the API for CORS (e.g. https://example.com)"
  type        = string
}

variable "ollama_base_url" {
  description = "HTTP URL of the Ollama instance reachable from ECS tasks"
  type        = string
}

variable "sqs_visibility_timeout" {
  description = "SQS VisibilityTimeout in seconds (must exceed Celery task timeout)"
  type        = number
  default     = 900
}

variable "artifact_lifecycle_days" {
  description = "Days before artifacts are deleted from the S3 artifact bucket"
  type        = number
  default     = 30
}

variable "github_org" {
  description = "GitHub organisation or username that owns this repository"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name (without the org prefix)"
  type        = string
}
