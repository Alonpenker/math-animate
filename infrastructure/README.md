# MathAnimate Infrastructure

Terraform infrastructure for the **math-animate** project deployed on AWS (`eu-north-1`) with Cloudflare as the public edge.

---

## Architecture

**Cloudflare** is the public edge. `mathanimate.com` is served by Cloudflare Pages. `api.mathanimate.com` is a proxied CNAME to the ALB — Cloudflare terminates TLS and forwards traffic to the ALB over HTTPS (Full strict mode). The ALB security group only accepts traffic from Cloudflare IPv4 ranges.

**ECS Fargate** hosts the stateless API container. It accepts HTTPS requests through the ALB, writes job records to RDS PostgreSQL, enqueues Manim render tasks on SQS, and reads/writes render artifacts on S3.

**EC2 (t3.medium, Amazon Linux 2023)** hosts the worker stack via `docker compose`. The compose file runs three services: `docker-daemon` (DinD for Manim rendering), `ollama` (embeddings at `http://ollama:11434`), and `worker` (Celery). The worker polls SQS, executes the Manim render pipeline, and uploads results to S3.

The frontend is deployed to Cloudflare Pages by `wrangler pages deploy` in CI.

```
  Browser
    │
    ▼
  Cloudflare edge
    │  mathanimate.com   → Cloudflare Pages (frontend SPA)
    │  api.mathanimate.com (CNAME proxied → ALB)
    │
    │ HTTPS (CF-Connecting-IP header injected)
    ▼
                          ┌─────────────────────────────────────────────────────────┐
                          │                    AWS eu-north-1                       │
                          │                                                         │
                          │  ┌──────────────────┐                                   │
                          │  │  ALB (public)     │  :443 (ACM cert) → ECS :8000     │
                          │  │  Cloudflare IPs   │  :80  → redirect to :443         │
                          │  │  only in SG       │                                  │
                          │  └────────┬─────────┘                                   │
                          │           │ port 8000                                   │
                          │           ▼                                             │
                          │  ┌──────────────────────────────────────────────────┐   │
                          │  │  Private Subnets  (eu-north-1a, eu-north-1b)     │   │
                          │  │                                                  │   │
                          │  │  ┌─────────────────────────────────────────┐     │   │
                          │  │  │  ECS Fargate  (api container :8000)     │     │   │
                          │  │  │  image: Docker Hub math-animate-backend │     │   │
                          │  │  │                                         │     │   │
                          │  │  │  ENV:                                   │     │   │
                          │  │  │    DATABASE_URL ──────────────────────► RDS   │   │
                          │  │  │    REDIS_URL ─────────────────────────► Redis │   │
                          │  │  │    SQS_QUEUE_URL ──── S3/SQS VPCEs ──► SQS    │   │
                          │  │  │    STORAGE_BUCKET ─────────────────── ► S3    │   │
                          │  │  │    FRONTEND_URL = https://mathanimate.com     │   │
                          │  │  │                                          │    │   │
                          │  │  │  Secrets (Secrets Manager VPCE):        │     │   │
                          │  │  │    api-key                              │     │   │
                          │  │  └──────────────────────────────────────── ┘     │   │
                          │  │                                                  │   │
                          │  │  ┌───────────────┐  ┌────────────┐  ┌─────────┐  │   │
                          │  │  │  RDS           │  │ElastiCache │  │   SQS   │ │   │
                          │  │  │  PostgreSQL 16 │  │ Redis 7.1  │  │  Queue  │ │   │
                          │  │  │  db.t3.micro   │  │cache.t3.micro│  │(jobs) │ │   │
                          │  │  │  :5432         │  │  :6379     │  │   DLQ   │ │   │
                          │  │  └───────────────┘  └────────────┘  └────┬────┘  │   │
                          │  │                                          │       │   │
                          │  │  ┌─────────────────────────────────────── ┐      │   │
                          │  │  │  EC2 Worker  t3.medium  AL2023          │◄─────┘  │
                          │  │  │  docker-compose (systemd)               │         │
                          │  │  │    docker-daemon  (DinD)                │         │
                          │  │  │    ollama         (:11434 embeddings)   │         │
                          │  │  │    worker         (Celery)              │         │
                          │  │  │                                         │         │
                          │  │  │  No inbound SG rules                    │         │
                          │  │  │  Updated via terraform apply            │         │
                          │  │  │                                         │         │
                          │  │  │  Secrets Manager VPCE:                  │         │
                          │  │  │    dockerhub-credentials, api-key       │         │
                          │  │  └────────────────────────┬────────────────┘         │
                          │  │                           │   S3 VPCE                │
                          │  │                           ▼                          │
                          │  │  ┌────────────────────────────────────────┐          │
                          │  │  │  S3 Artifact Bucket                    │          │
                          │  │  │  mathanimate-artifacts-prod            │          │
                          │  │  │  AES-256 SSE, 30-day lifecycle expiry  │          │
                          │  │  └────────────────────────────────────────┘          │
                          │  │                                                  │   │
                          │  │  VPC Endpoints:                                  │   │
                          │  │    Gateway : s3                                  │   │
                          │  │    Interface: sqs, secretsmanager, logs          │   │
                          │  └──────────────────────────────────────────────────┘   │
                          └─────────────────────────────────────────────────────────┘
```

---

## Service Communication Map

| From | To | Port | Mechanism |
|------|----|------|-----------|
| Browser | Cloudflare Pages | :443 | `mathanimate.com` — Cloudflare Pages CDN |
| Browser | Cloudflare edge | :443 | `api.mathanimate.com` — Cloudflare proxy |
| Cloudflare | ALB | :443 | Cloudflare IPv4 ranges only (ALB SG locked) |
| ALB | ECS API | :8000 | Private subnet, `alb` → `ecs_api` SG rule |
| ECS API | RDS | :5432 | Private subnet, `ecs_api` → `rds` SG rule |
| ECS API | Redis | :6379 | Private subnet, `ecs_api` → `redis` SG rule |
| ECS API | SQS | :443 | SQS interface VPC endpoint |
| ECS API | S3 | :443 | S3 gateway VPC endpoint |
| ECS API | Secrets Manager | :443 | Secrets Manager interface VPC endpoint |
| ECS API | Docker Hub | :443 | NAT gateway → internet (image pull on task start) |
| EC2 Worker | SQS | :443 | SQS interface VPC endpoint |
| EC2 Worker | S3 | :443 | S3 gateway VPC endpoint |
| EC2 Worker | RDS | :5432 | Private subnet, `ec2_worker` → `rds` SG rule |
| EC2 Worker | Redis | :6379 | Private subnet, `ec2_worker` → `redis` SG rule |
| EC2 Worker | Secrets Manager | :443 | Secrets Manager interface VPC endpoint |
| EC2 Worker | Docker Hub | :443 | NAT gateway → internet |
| EC2 Worker | CloudWatch Logs | :443 | CloudWatch Logs interface VPC endpoint |


---

## One-Time Setup

Must happen before the first `terraform apply`.

### 1. Create Terraform state backend

```bash
# S3 state bucket
aws s3api create-bucket \
  --bucket mathanimate-tf-state \
  --region eu-north-1 \
  --create-bucket-configuration LocationConstraint=eu-north-1

aws s3api put-bucket-versioning \
  --bucket mathanimate-tf-state \
  --versioning-configuration Status=Enabled

aws s3api put-bucket-encryption \
  --bucket mathanimate-tf-state \
  --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# DynamoDB lock table
aws dynamodb create-table \
  --table-name mathanimate-tf-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-north-1
```

### 2. Create GitHub Actions OIDC provider

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 3. Create required secrets

See [`infrastructure/scripts/provision-secrets.md`](scripts/provision-secrets.md) for the full commands. Summary:

| Secret | Notes |
|--------|-------|
| `mathanimate/prod/db-password` | Strong password. |
| `mathanimate/prod/x-api-key` | Generated JWT secret. |
| `mathanimate/prod/openai-api-key` | OpenAI secret key (`sk-...`). |
| `mathanimate/prod/dockerhub-credentials` | JSON `{"username":"<username>","password":"<hub-token>"}`. |
| `mathanimate/prod/cloudflare-credentials` | JSON `{"api_token":"...","zone_id":"...","account_id":"..."}`. |

---

## First Deploy Sequence

```
1. terraform init && terraform apply     (from infrastructure/envs/prod/)
2. Set GitHub secrets (see table below)
3. Push to main or trigger deploy.yml manually
```

### GitHub repository secrets

| Secret | Value |
|---|---|
| `AWS_ROLE_ARN` | `terraform output -raw github_actions_role_arn` |

---

## Day-to-Day Operations

### Deploy application

Trigger `deploy.yml` manually (workflow dispatch):

```
build-and-push
    └── deploy-api        (ECS force-new-deployment; waits for stable)
         ├── run-migrations
         │    └── seed-knowledge
         └── deploy-frontend  (builds with VITE_API_BASE_URL=https://api.mathanimate.com/api/v1; deploys to Cloudflare Pages)
```

Worker updates (new Docker image) require a Terraform apply — the EC2 instance is recreated with the new `image_uri`:

```bash
terraform apply -target=module.ec2_worker
```

### Local development

The frontend `.env.production` uses a relative `/api/v1` path for VPS builds. For local testing against the production API, set `VITE_API_BASE_URL=https://api.mathanimate.com/api/v1` in your shell before running `npm run build`.

### Update infrastructure

Trigger `terraform.yml` manually (workflow dispatch).

### Pause (cost saving)

Trigger `pause.yml` manually. Type `PAUSE` in the confirmation field.

Destroys all metered resources: `ecs`, `ec2_worker`, `alb`, `rds`, `elasticache`, `sqs`, `security_groups`, `networking`.

Preserves: `iam`, `s3`, Secrets Manager entries, Docker Hub images.

### Resume

1. Trigger `terraform.yml` (manual dispatch) — re-provisions infrastructure.
2. Trigger `deploy.yml` (manual dispatch) — redeploys application.

---

## Accessing the Stack

| Resource | URL / Command |
|----------|---------------|
| API base URL | `https://api.mathanimate.com/api/v1` |
| Frontend | `https://mathanimate.com` (Cloudflare Pages) |
| API logs | CloudWatch log group `/mathanimate/ecs/api` (3-day retention) |
| Worker logs | CloudWatch log group `/mathanimate/ec2/worker` (3-day retention) |
| Terraform outputs | `terraform output` from `infrastructure/envs/prod/` |
