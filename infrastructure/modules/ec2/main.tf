data "aws_region" "current" {}

# ── CloudWatch Log Group for worker ───────────────────────────────────────────
resource "aws_cloudwatch_log_group" "worker" {
  name              = "/mathanimate/ec2/worker"
  retention_in_days = 14

  tags = {
    Name = "/mathanimate/ec2/worker"
  }
}

# ── EC2 Instance ───────────────────────────────────────────────────────────────
resource "aws_instance" "worker" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.private_subnet_ids[0]
  vpc_security_group_ids = [var.worker_sg_id]
  iam_instance_profile   = var.instance_profile_name
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
    worker_image_uri     = var.image_uri
    artifact_bucket_name = var.artifact_bucket_name
    sqs_queue_url        = var.sqs_queue_url
    database_url         = var.database_url
    redis_url            = var.redis_url
    docker_compose_content = var.docker_compose_content
    log_group_name         = aws_cloudwatch_log_group.worker.name
  }))

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # IMDSv2
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "${var.name_prefix}-ec2-worker"
  }

  lifecycle {
    ignore_changes = [user_data, ami]
  }
}
