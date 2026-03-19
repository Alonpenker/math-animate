# ── ALB Security Group ────────────────────────────────────────────────────────
resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-sg-alb"
  description = "ALB: allow HTTPS inbound from internet, HTTP for demo"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP redirect / demo listener
  ingress {
    description = "HTTP from internet (redirect or demo)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-sg-alb"
  }
}

# ── ECS API Security Group ─────────────────────────────────────────────────────
resource "aws_security_group" "ecs_api" {
  name        = "${var.name_prefix}-sg-ecs-api"
  description = "ECS API: receive from ALB, egress to data layer"
  vpc_id      = var.vpc_id

  # HTTPS to AWS VPC endpoints (SQS, Secrets Manager, CloudWatch, S3) and Docker Hub
  egress {
    description = "HTTPS to AWS endpoints and Docker Hub"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-sg-ecs-api"
  }
}

# ── EC2 Worker Security Group ──────────────────────────────────────────────────
resource "aws_security_group" "ec2_worker" {
  name        = "${var.name_prefix}-sg-ec2-worker"
  description = "EC2 Worker: no inbound (SSM only), egress to data layer"
  vpc_id      = var.vpc_id

  # No inbound rules — management only via SSM Session Manager

  egress {
    description = "HTTPS to AWS endpoints and Docker Hub"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-sg-ec2-worker"
  }
}

# ── RDS Security Group ─────────────────────────────────────────────────────────
resource "aws_security_group" "rds" {
  name        = "${var.name_prefix}-sg-rds"
  description = "RDS PostgreSQL: accept from ECS API and EC2 worker"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name_prefix}-sg-rds"
  }
}

# ── Redis Security Group ───────────────────────────────────────────────────────
resource "aws_security_group" "redis" {
  name        = "${var.name_prefix}-sg-redis"
  description = "ElastiCache Redis: accept from ECS API and EC2 worker"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name_prefix}-sg-redis"
  }
}

# ── Inter-Security-Group Rules (split out to avoid dependency cycles) ──────────
resource "aws_vpc_security_group_egress_rule" "alb_to_ecs_api_8000" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.ecs_api.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
  description                  = "Forward to ECS API"
}

resource "aws_vpc_security_group_ingress_rule" "ecs_api_from_alb_8000" {
  security_group_id            = aws_security_group.ecs_api.id
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
  description                  = "API traffic from ALB"
}

resource "aws_vpc_security_group_egress_rule" "ecs_api_to_rds_5432" {
  security_group_id            = aws_security_group.ecs_api.id
  referenced_security_group_id = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  description                  = "PostgreSQL to RDS"
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs_api_5432" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.ecs_api.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  description                  = "PostgreSQL from ECS API"
}

resource "aws_vpc_security_group_egress_rule" "ec2_worker_to_rds_5432" {
  security_group_id            = aws_security_group.ec2_worker.id
  referenced_security_group_id = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  description                  = "PostgreSQL to RDS"
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_ec2_worker_5432" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.ec2_worker.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  description                  = "PostgreSQL from EC2 worker"
}

resource "aws_vpc_security_group_egress_rule" "ecs_api_to_redis_6379" {
  security_group_id            = aws_security_group.ecs_api.id
  referenced_security_group_id = aws_security_group.redis.id
  ip_protocol                  = "tcp"
  from_port                    = 6379
  to_port                      = 6379
  description                  = "Redis to ElastiCache"
}

resource "aws_vpc_security_group_ingress_rule" "redis_from_ecs_api_6379" {
  security_group_id            = aws_security_group.redis.id
  referenced_security_group_id = aws_security_group.ecs_api.id
  ip_protocol                  = "tcp"
  from_port                    = 6379
  to_port                      = 6379
  description                  = "Redis from ECS API"
}

resource "aws_vpc_security_group_egress_rule" "ec2_worker_to_redis_6379" {
  security_group_id            = aws_security_group.ec2_worker.id
  referenced_security_group_id = aws_security_group.redis.id
  ip_protocol                  = "tcp"
  from_port                    = 6379
  to_port                      = 6379
  description                  = "Redis to ElastiCache"
}

resource "aws_vpc_security_group_ingress_rule" "redis_from_ec2_worker_6379" {
  security_group_id            = aws_security_group.redis.id
  referenced_security_group_id = aws_security_group.ec2_worker.id
  ip_protocol                  = "tcp"
  from_port                    = 6379
  to_port                      = 6379
  description                  = "Redis from EC2 worker"
}

# ── VPC Endpoint Security Group ────────────────────────────────────────────────
resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.name_prefix}-sg-vpc-endpoints"
  description = "Interface VPC endpoints: accept HTTPS from private subnets"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-sg-vpc-endpoints"
  }
}
