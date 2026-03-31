variable "zone_id" {
  description = "Cloudflare zone ID for mathanimate.com"
  type        = string
}

variable "alb_dns_name" {
  description = "DNS name of the ALB — target for the api.mathanimate.com CNAME"
  type        = string
}
