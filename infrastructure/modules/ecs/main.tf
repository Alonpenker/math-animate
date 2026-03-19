data "aws_region" "current" {}

# ── CloudWatch Log Group ───────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "api" {
  name              = "/mathanimate/ecs/api"
  retention_in_days = 14

  tags = {
    Name = "/mathanimate/ecs/api"
  }
}

# ── ECS Cluster ────────────────────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.name_prefix}-cluster"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

# ── Task Definition ────────────────────────────────────────────────────────────
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = var.image_uri

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "ENVIRONMENT", value = "prod" },
        { name = "AWS_REGION", value = data.aws_region.current.name },
        { name = "BROKER_URL", value = "sqs://" },
        { name = "SQS_QUEUE_URL", value = var.sqs_queue_url },
        { name = "STORAGE_BUCKET", value = var.artifact_bucket_name },
        { name = "STORAGE_ENDPOINT", value = "s3.amazonaws.com" },
        { name = "DATABASE_URL", value = var.database_url },
        { name = "REDIS_URL", value = var.redis_url },
        { name = "FRONTEND_URL", value = var.frontend_url },
      ]

      # ECS secrets injection: valueFrom accepts secret ARN or secret name.
      # Using the secret name (path) is simpler and avoids the ARN random suffix.
      # The execution role policy already grants access to mathanimate/<env>/* secrets.
      secrets = [
        {
          name      = "API_KEY"
          valueFrom = "mathanimate/${var.environment}/api-key"
        },
        {
          name      = "STORAGE_ACCESS_KEY"
          valueFrom = "mathanimate/${var.environment}/storage-access-key"
        },
        {
          name      = "STORAGE_SECRET_KEY"
          valueFrom = "mathanimate/${var.environment}/storage-secret-key"
        },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "api"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -sf http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }

      repositoryCredentials = {
        credentialsParameter = var.dockerhub_credentials_secret_arn
      }

      essential = true
    }
  ])

  tags = {
    Name = "${var.name_prefix}-api-task"
  }
}

# ── ECS Service ────────────────────────────────────────────────────────────────
resource "aws_ecs_service" "api" {
  name            = "${var.name_prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_api_sg_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_controller {
    type = "ECS"
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = false # Let GitHub Actions handle rollback decisions
  }

  health_check_grace_period_seconds = 120

  # Ignore task definition changes from outside Terraform (GitHub Actions deploys)
  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = {
    Name = "${var.name_prefix}-api-service"
  }
}
