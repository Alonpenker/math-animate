resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.name_prefix}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.name_prefix}-redis-subnet-group"
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${var.name_prefix}-redis"
  description          = "Redis for Celery result backend and rate limiting"

  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.node_type
  num_cache_clusters   = 1
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [var.redis_sg_id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false # Disable TLS to avoid redis:// vs rediss:// complexity

  automatic_failover_enabled = false # Single-node, no failover needed
  multi_az_enabled           = false

  snapshot_retention_limit = 1
  snapshot_window          = "03:00-04:00"
  maintenance_window       = "mon:04:00-mon:05:00"

  apply_immediately = true

  tags = {
    Name = "${var.name_prefix}-redis"
  }
}
