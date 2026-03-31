# Secrets Setup

Run these commands once before the first `terraform apply`.
All secrets live under `mathanimate/prod/` in `eu-north-1`.

---

## 1. db-password

Must exist **before** `terraform apply` — Terraform reads it at plan time.

```bash
aws secretsmanager create-secret \
  --region eu-north-1 \
  --name "mathanimate/prod/db-password" \
  --description "RDS master password" \
  --secret-string "YOUR_STRONG_PASSWORD"
```

---

## 2. x-api-key

Gate key for the MathAnimate REST API (`X-API-Key` header):

```bash
aws secretsmanager create-secret \
  --region eu-north-1 \
  --name "mathanimate/prod/x-api-key" \
  --description "X-API-Key for the MathAnimate REST API" \
  --secret-string "YOUR_X_API_KEY"
```

To retrieve the generated value later (e.g. to configure local dev or the frontend):

```bash
aws secretsmanager get-secret-value \
  --region eu-north-1 \
  --secret-id "mathanimate/prod/x-api-key" \
  --query SecretString --output text
```

---

## 3. openai-api-key

```bash
aws secretsmanager create-secret \
  --region eu-north-1 \
  --name "mathanimate/prod/openai-api-key" \
  --description "OpenAI API key for LLM plan and code generation" \
  --secret-string "sk-..."
```

---

## 4. dockerhub-credentials

Used by ECS (`repositoryCredentials`), EC2 user data (`docker login`), and CI (image push).

```bash
aws secretsmanager create-secret \
  --region eu-north-1 \
  --name "mathanimate/prod/dockerhub-credentials" \
  --description "Docker Hub credentials for image pull and push" \
  --secret-string '{"username":"YOUR_DOCKERHUB_USERNAME","password":"YOUR_DOCKERHUB_TOKEN"}'
```

---

## 5. cloudflare-credentials

Used by Terraform (provider + zone lookups) and CI (wrangler Pages deploy).

```bash
aws secretsmanager create-secret \
  --region eu-north-1 \
  --name "mathanimate/prod/cloudflare-credentials" \
  --description "Cloudflare API token, zone ID, and account ID" \
  --secret-string '{"api_token":"YOUR_CF_API_TOKEN","zone_id":"YOUR_CF_ZONE_ID","account_id":"YOUR_CF_ACCOUNT_ID"}'
```
