# ── api.mathanimate.com ────────────────────────────────────────────────────────
# Proxied CNAME so Cloudflare acts as the TLS termination edge for the API.
# The mathanimate.com apex record is managed automatically by Cloudflare Pages
# when the custom domain is attached — do NOT add a record for it here.
resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = "api"
  type    = "CNAME"
  content = var.alb_dns_name
  proxied = true
  ttl     = 1 # TTL is auto when proxied = true; 1 is the Cloudflare convention
}
