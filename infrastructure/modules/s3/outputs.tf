output "artifact_bucket_name" {
  description = "Artifact S3 bucket name"
  value       = aws_s3_bucket.artifacts.id
}

output "artifact_bucket_arn" {
  description = "Artifact S3 bucket ARN"
  value       = aws_s3_bucket.artifacts.arn
}
