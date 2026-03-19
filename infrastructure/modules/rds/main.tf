resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>?"
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "mathanimate/${var.environment}/db-password"
  description             = "RDS master password for the mathanimate database"
  recovery_window_in_days = 0 # Allows immediate deletion when pausing/destroying

  tags = {
    Name = "${var.name_prefix}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db.result
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.name_prefix}-rds-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.name_prefix}-rds-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.name_prefix}-postgres"

  engine               = "postgres"
  engine_version       = "16"
  instance_class       = var.instance_class
  allocated_storage    = 20
  max_allocated_storage = 100
  storage_type         = "gp3"
  storage_encrypted    = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_sg_id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  deletion_protection = false # Set to true before running production workloads
  skip_final_snapshot = true

  # Enable Performance Insights for query analysis
  performance_insights_enabled = false # t3.micro doesn't support PI with free tier

  parameter_group_name = aws_db_parameter_group.main.name

  tags = {
    Name = "${var.name_prefix}-postgres"
  }
}

resource "aws_db_parameter_group" "main" {
  name   = "${var.name_prefix}-pg16-params"
  family = "postgres16"

  # Shared preload libraries: pgvector does not require shared_preload_libraries
  # but we include pg_stat_statements for query monitoring
  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "${var.name_prefix}-pg16-params"
  }
}
