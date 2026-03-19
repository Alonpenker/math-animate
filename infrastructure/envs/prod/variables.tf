variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["eu-north-1a", "eu-north-1b"]
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_name" {
  type    = string
  default = "mathanimate"
}

variable "db_username" {
  type    = string
  default = "mathanimate"
}

variable "cache_node_type" {
  type    = string
  default = "cache.t3.micro"
}

variable "sqs_visibility_timeout" {
  type    = number
  default = 900
}

variable "api_cpu" {
  type    = number
  default = 512
}

variable "api_memory" {
  type    = number
  default = 1024
}

variable "api_desired_count" {
  type    = number
  default = 1
}

variable "worker_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "worker_ami_id" {
  type = string
}

variable "artifact_lifecycle_days" {
  type    = number
  default = 30
}

variable "alb_certificate_arn" {
  type    = string
  default = ""
}

variable "image_uri" {
  description = "Docker Hub image URI for the backend (e.g. youruser/math-animate-backend:abc1234)"
  type        = string
}

variable "dockerhub_credentials_secret_arn" {
  description = "Secrets Manager ARN for Docker Hub credentials used by ECS to pull images"
  type        = string
}

variable "github_org" {
  type = string
}

variable "github_repo" {
  type = string
}
