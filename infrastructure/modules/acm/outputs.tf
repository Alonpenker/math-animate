output "certificate_arn" {
  description = "ARN of the validated ACM certificate for api.mathanimate.com"
  value       = aws_acm_certificate_validation.api.certificate_arn
}
