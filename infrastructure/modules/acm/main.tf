# ── ACM Certificate for api.mathanimate.com ────────────────────────────────────
resource "aws_acm_certificate" "api" {
  domain_name       = "api.mathanimate.com"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "api.mathanimate.com"
  }
}

# ── Cloudflare DNS validation records ──────────────────────────────────────────
# One CNAME per domain_validation_options entry (usually just one for a single
# domain cert). Not proxied — ACM validation must reach the record directly.
resource "cloudflare_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api.domain_validation_options :
    dvo.domain_name => dvo
  }

  zone_id = var.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  content = each.value.resource_record_value
  proxied = false
  ttl     = 60
}

# ── Wait for certificate validation ───────────────────────────────────────────
resource "aws_acm_certificate_validation" "api" {
  certificate_arn         = aws_acm_certificate.api.arn
  validation_record_fqdns = [for record in cloudflare_record.acm_validation : record.hostname]
}
