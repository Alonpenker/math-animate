variable "name_prefix" {
  description = "Prefix applied to all resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where security groups are created"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block (used for VPC endpoint ingress rule)"
  type        = string
}
