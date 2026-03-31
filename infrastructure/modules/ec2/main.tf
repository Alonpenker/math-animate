data "aws_region" "current" {}

# ── CloudWatch Log Group for worker ───────────────────────────────────────────
resource "aws_cloudwatch_log_group" "worker" {
  name              = "/mathanimate/ec2/worker"
  retention_in_days = 3

  tags = {
    Name = "/mathanimate/ec2/worker"
  }
}

# ── Upload docker-compose.ec2.yml to S3 ───────────────────────────────────────
# Terraform uploads the compose file on every apply so the instance can download
# it fresh during user-data. The aws_instance depends on this resource implicitly
# because compose_s3_key is referenced in the templatefile() call.
resource "aws_s3_object" "docker_compose" {
  bucket = var.artifact_bucket_name
  key    = "config/docker-compose.ec2.yml"
  source = "${path.module}/docker-compose.ec2.yml"
  etag   = filemd5("${path.module}/docker-compose.ec2.yml")
}

# ── EC2 Instance ───────────────────────────────────────────────────────────────
resource "aws_instance" "worker" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.private_subnet_ids[0]
  vpc_security_group_ids      = [var.worker_sg_id]
  iam_instance_profile        = var.instance_profile_name
  associate_public_ip_address = false

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 50 # GB — needs space for Docker images and render artifacts
    delete_on_termination = true
    encrypted             = true
  }

  user_data = base64encode(templatefile("${path.module}/userdata.sh.tpl", {
    aws_region           = data.aws_region.current.name
    environment          = var.environment
    frontend_url         = var.frontend_url
    worker_image_uri     = var.image_uri
    artifact_bucket_name = var.artifact_bucket_name
    sqs_queue_url        = var.sqs_queue_url
    database_url         = var.database_url
    redis_url            = var.redis_url
    log_group_name       = var.log_group_name
    compose_s3_key       = aws_s3_object.docker_compose.key
    storage_access_key   = var.storage_access_key
    storage_secret_key   = var.storage_secret_key
  }))

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2
    http_put_response_hop_limit = 1
  }

  timeouts {
    create = "10m"
    update = "10m"
    delete = "5m"
  }

  tags = {
    Name = "${var.name_prefix}-ec2-worker"
  }
}

# ── Worker Readiness Alarms ────────────────────────────────────────────────────
locals {
  worker_checks = {
    DockerDaemonReady = "Docker daemon running and Manim image pulled"
    OllamaModelReady  = "Ollama running and nomic-embed-text model downloaded"
    CeleryWorkerReady = "Celery worker container running"
  }
}

resource "aws_cloudwatch_metric_alarm" "worker_readiness" {
  for_each = local.worker_checks

  alarm_name          = "${var.name_prefix}-${each.key}"
  alarm_description   = each.value
  namespace           = "MathAnimate/Worker"
  metric_name         = each.key
  dimensions          = { InstanceId = aws_instance.worker.id }
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${var.name_prefix}-${each.key}"
  }
}
