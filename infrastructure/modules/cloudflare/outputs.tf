output "api_record_hostname" {
  description = "Fully-qualified hostname of the api.mathanimate.com Cloudflare record"
  value       = cloudflare_record.api.hostname
}
