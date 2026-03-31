output "alb_sg_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "ecs_api_sg_id" {
  description = "ECS API task security group ID"
  value       = aws_security_group.ecs_api.id
}

output "ec2_worker_sg_id" {
  description = "EC2 worker instance security group ID"
  value       = aws_security_group.ec2_worker.id
}

output "rds_sg_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "redis_sg_id" {
  description = "ElastiCache Redis security group ID"
  value       = aws_security_group.redis.id
}

output "vpc_endpoints_sg_id" {
  description = "VPC interface endpoints security group ID"
  value       = aws_security_group.vpc_endpoints.id
}
