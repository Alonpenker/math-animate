variable "name_prefix" {
  description = "Prefix applied to all resource names"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "artifact_bucket_name" {
  description = "Name of the S3 artifact bucket"
  type        = string
}

variable "frontend_bucket_name" {
  description = "Name of the S3 frontend bucket"
  type        = string
}

variable "github_org" {
  description = "GitHub organisation or username"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}
