variable "visibility_timeout" {
  description = "SQS message visibility timeout in seconds (must exceed Celery task timeout)"
  type        = number
  default     = 900
}

variable "ecs_task_role_arn" {
  description = "ARN of the ECS task role (for queue policy)"
  type        = string
}

variable "ec2_worker_role_arn" {
  description = "ARN of the EC2 worker IAM role (for queue policy)"
  type        = string
}
