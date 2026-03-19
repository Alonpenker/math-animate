variable "environment" {
  description = "Deployment environment (used in bucket names)"
  type        = string
}

variable "lifecycle_days" {
  description = "Days before objects in the artifact bucket are deleted"
  type        = number
  default     = 30
}
