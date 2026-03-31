data "aws_caller_identity" "current" {}

# ── Artifact Bucket ────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "artifacts" {
  bucket        = "mathanimate-artifacts-${var.environment}"
  force_destroy = true # Allow destroy even when bucket has objects

  tags = {
    Name    = "mathanimate-artifacts-${var.environment}"
    Purpose = "job-artifacts"
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "delete-old-artifacts"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = var.lifecycle_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

