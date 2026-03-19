output "artifact_bucket_name" {
  description = "Artifact S3 bucket name"
  value       = aws_s3_bucket.artifacts.id
}

output "artifact_bucket_arn" {
  description = "Artifact S3 bucket ARN"
  value       = aws_s3_bucket.artifacts.arn
}

output "frontend_bucket_name" {
  description = "Frontend S3 bucket name"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "Frontend S3 bucket ARN"
  value       = aws_s3_bucket.frontend.arn
}

output "frontend_bucket_regional_domain" {
  description = "Frontend bucket regional domain name"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}
