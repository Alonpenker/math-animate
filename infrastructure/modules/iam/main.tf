data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# ── ECS Execution Role ────────────────────────────────────────────────────────
# Used by the ECS control plane to pull images and ship logs.
resource "aws_iam_role" "ecs_execution" {
  name               = "${var.name_prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow ECS execution role to read any secrets with the mathanimate/ prefix
data "aws_iam_policy_document" "ecs_execution_secrets" {
  statement {
    sid     = "ReadMathAnimateSecrets"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:mathanimate/${var.environment}/*",
    ]
  }
}

resource "aws_iam_policy" "ecs_execution_secrets" {
  name   = "${var.name_prefix}-ecs-execution-secrets"
  policy = data.aws_iam_policy_document.ecs_execution_secrets.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_secrets" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = aws_iam_policy.ecs_execution_secrets.arn
}

# ── ECS Task Role (API runtime permissions) ────────────────────────────────────
resource "aws_iam_role" "ecs_task" {
  name               = "${var.name_prefix}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json
}

data "aws_iam_policy_document" "ecs_task" {
  # Artifact S3 bucket read/write
  statement {
    sid     = "ArtifactBucketAccess"
    actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = [
      "arn:aws:s3:::${var.artifact_bucket_name}",
      "arn:aws:s3:::${var.artifact_bucket_name}/*",
    ]
  }

  # SQS — send messages to the job queue
  statement {
    sid     = "SQSSend"
    actions = ["sqs:SendMessage", "sqs:GetQueueAttributes", "sqs:GetQueueUrl"]
    resources = [
      "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:mathanimate-jobs",
      "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:mathanimate-jobs-dlq",
    ]
  }

  # Secrets Manager — read own secrets
  statement {
    sid     = "ReadMathAnimateSecrets"
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:mathanimate/${var.environment}/*",
    ]
  }
}

resource "aws_iam_policy" "ecs_task" {
  name   = "${var.name_prefix}-ecs-task-policy"
  policy = data.aws_iam_policy_document.ecs_task.json
}

resource "aws_iam_role_policy_attachment" "ecs_task" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_task.arn
}

# ── EC2 Instance Role (Worker runtime permissions) ─────────────────────────────
resource "aws_iam_role" "ec2_worker" {
  name               = "${var.name_prefix}-ec2-worker-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

data "aws_iam_policy_document" "ec2_worker" {
  # Artifact S3 bucket read/write
  statement {
    sid     = "ArtifactBucketAccess"
    actions = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = [
      "arn:aws:s3:::${var.artifact_bucket_name}",
      "arn:aws:s3:::${var.artifact_bucket_name}/*",
    ]
  }

  # SQS — receive and delete messages from the job queue
  statement {
    sid = "SQSWorker"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
    ]
    resources = [
      "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:mathanimate-jobs",
      "arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:mathanimate-jobs-dlq",
    ]
  }

  # Secrets Manager — read own secrets
  statement {
    sid     = "ReadMathAnimateSecrets"
    actions = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = [
      "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:mathanimate/${var.environment}/*",
    ]
  }

  # CloudWatch Logs — ship instance logs
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]
    resources = ["arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/mathanimate/*"]
  }
}

resource "aws_iam_policy" "ec2_worker" {
  name   = "${var.name_prefix}-ec2-worker-policy"
  policy = data.aws_iam_policy_document.ec2_worker.json
}

resource "aws_iam_role_policy_attachment" "ec2_worker" {
  role       = aws_iam_role.ec2_worker.name
  policy_arn = aws_iam_policy.ec2_worker.arn
}

# Attach SSM managed policy so the instance is reachable via Session Manager
resource "aws_iam_role_policy_attachment" "ec2_worker_ssm" {
  role       = aws_iam_role.ec2_worker.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_worker" {
  name = "${var.name_prefix}-ec2-worker-profile"
  role = aws_iam_role.ec2_worker.name
}

# ── GitHub Actions OIDC Role ───────────────────────────────────────────────────
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "${var.name_prefix}-github-actions-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json
}

data "aws_iam_policy_document" "github_actions" {
  # ECS — deploy new task revisions
  statement {
    sid = "ECSdeploy"
    actions = [
      "ecs:UpdateService",
      "ecs:RunTask",
      "ecs:DescribeTasks",
      "ecs:DescribeServices",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:ListTasks",
    ]
    resources = ["*"]
  }

  # SSM — send commands to worker EC2
  statement {
    sid       = "SSMSendCommand"
    actions   = ["ssm:SendCommand", "ssm:GetCommandInvocation"]
    resources = ["*"]
  }

  # S3 — sync frontend build
  statement {
    sid     = "FrontendS3Sync"
    actions = ["s3:PutObject", "s3:DeleteObject", "s3:ListBucket", "s3:GetObject"]
    resources = [
      "arn:aws:s3:::${var.frontend_bucket_name}",
      "arn:aws:s3:::${var.frontend_bucket_name}/*",
    ]
  }

  # IAM PassRole — needed for ECS run-task to pass task execution role
  statement {
    sid       = "IAMPassRole"
    actions   = ["iam:PassRole"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }

  # Terraform state management
  statement {
    sid = "TerraformState"
    actions = [
      "s3:GetObject", "s3:PutObject", "s3:DeleteObject",
      "s3:ListBucket", "s3:GetBucketVersioning",
    ]
    resources = [
      "arn:aws:s3:::mathanimate-tf-state",
      "arn:aws:s3:::mathanimate-tf-state/*",
    ]
  }

  statement {
    sid = "TerraformLock"
    actions = [
      "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
    ]
    resources = [
      "arn:aws:dynamodb:${var.aws_region}:${var.aws_account_id}:table/mathanimate-tf-locks",
    ]
  }

  # Full infrastructure management for terraform apply/destroy
  statement {
    sid       = "InfrastructureManagement"
    actions   = ["*"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:RequestedRegion"
      values   = [var.aws_region]
    }
  }
}

resource "aws_iam_policy" "github_actions" {
  name   = "${var.name_prefix}-github-actions-policy"
  policy = data.aws_iam_policy_document.github_actions.json
}

resource "aws_iam_role_policy_attachment" "github_actions" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions.arn
}
