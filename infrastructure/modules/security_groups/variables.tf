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

variable "allowed_ingress_cidrs" {
  description = "List of CIDRs allowed to reach the ALB on ports 80 and 443 (Cloudflare IPv4 ranges)"
  type        = list(string)
}
