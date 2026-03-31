# ── ALB Security Group ────────────────────────────────────────────────────────
resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-sg-alb"
  description = "ALB: allow HTTPS and HTTP inbound from Cloudflare IP ranges only"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name_prefix}-sg-alb"
  }

  timeouts {
    delete = "5m"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_https_cloudflare" {
  for_each = toset(var.allowed_ingress_cidrs)

  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "HTTPS from Cloudflare ${each.value}"
}

resource "aws_vpc_security_group_ingress_rule" "alb_http_cloudflare" {
  for_each = toset(var.allowed_ingress_cidrs)

  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  description       = "HTTP from Cloudflare ${each.value}"
}

# ── ECS API Security Group ─────────────────────────────────────────────────────
resource "aws_security_group" "ecs_api" {
  name        = "${var.name_prefix}-sg-ecs-api"
  description = "ECS API: receive from ALB, egress to data layer"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name_prefix}-sg-ecs-api"
  }

  timeouts {
    delete = "5m"
  }
}

# ── EC2 Worker Security Group ──────────────────────────────────────────────────
resource "aws_security_group" "ec2_worker" {
  name        = "${var.name_prefix}-sg-ec2-worker"
  description = "EC2 Worker: no inbound, egress to data layer"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.name_prefix}-sg-ec2-worker"
  }

  timeouts {
    delete = "5m"
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

  timeouts {
    delete = "5m"
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

  timeouts {
    delete = "5m"
  }
}

# ── ECS API egress: HTTPS (Secrets Manager, SQS, DockerHub) ───────────────────
resource "aws_vpc_security_group_egress_rule" "ecs_api_https" {
  security_group_id = aws_security_group.ecs_api.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "HTTPS to AWS endpoints and Docker Hub"
}

# ── EC2 Worker egress: HTTPS (Secrets Manager, SQS, DockerHub, S3) ────────────
resource "aws_vpc_security_group_egress_rule" "ec2_worker_https" {
  security_group_id = aws_security_group.ec2_worker.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "HTTPS to AWS endpoints and Docker Hub"
}

# ── EC2 Worker egress: HTTP (Docker image pulls from registries) ───────────────
resource "aws_vpc_security_group_egress_rule" "ec2_worker_http" {
  security_group_id = aws_security_group.ec2_worker.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  description       = "HTTP for Docker image pulls"
}

# ── Inter-Security-Group Rules ──────────
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
