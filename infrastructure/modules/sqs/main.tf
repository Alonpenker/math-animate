# ── Dead Letter Queue ─────────────────────────────────────────────────────────
resource "aws_sqs_queue" "dlq" {
  name                       = "mathanimate-jobs-dlq"
  message_retention_seconds  = 1209600 # 14 days
  visibility_timeout_seconds = var.visibility_timeout

  tags = {
    Name = "mathanimate-jobs-dlq"
  }
}

# ── Main Queue ─────────────────────────────────────────────────────────────────
resource "aws_sqs_queue" "main" {
  name                       = "mathanimate-jobs"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = 86400 # 1 day
  receive_wait_time_seconds  = 20    # Enable long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "mathanimate-jobs"
  }
}

# ── Queue Policies (allow ECS task role and EC2 worker role to use queues) ─────
data "aws_iam_policy_document" "main_queue_access" {
  statement {
    sid    = "AllowAppRoles"
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        var.ecs_task_role_arn,
        var.ec2_worker_role_arn,
      ]
    }
    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
    ]
    resources = [aws_sqs_queue.main.arn]
  }
}

data "aws_iam_policy_document" "dlq_access" {
  statement {
    sid    = "AllowAppRoles"
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        var.ecs_task_role_arn,
        var.ec2_worker_role_arn,
      ]
    }
    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
    ]
    resources = [aws_sqs_queue.dlq.arn]
  }
}

resource "aws_sqs_queue_policy" "main" {
  queue_url = aws_sqs_queue.main.id
  policy    = data.aws_iam_policy_document.main_queue_access.json
}

resource "aws_sqs_queue_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  policy    = data.aws_iam_policy_document.dlq_access.json
}
