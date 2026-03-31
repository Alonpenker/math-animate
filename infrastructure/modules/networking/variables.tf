variable "name_prefix" {
  description = "Prefix applied to all resource names"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "availability_zones" {
  description = "List of AZs to deploy subnets into"
  type        = list(string)
}

variable "endpoint_security_group_ids" {
  description = "Security group IDs to attach to interface VPC endpoints. Pass an empty list on first apply; Terraform will resolve the actual IDs on the next apply via the security_groups module."
  type        = list(string)
  default     = []
}
