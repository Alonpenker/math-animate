# Infrastructure — CLAUDE.md

Terraform infrastructure for the **math-animate** project, targeting AWS.

## Stack

- **IaC:** Terraform >= 1.6.0 (CI pins `TF_VERSION: "1.13.3"` in `.github/workflows/apply.yml`)
- **Remote state:** S3 bucket `mathanimate-tf-state`, DynamoDB lock table `mathanimate-tf-locks`, region `eu-north-1`, encryption enabled
- **Default region:** `eu-north-1` (Stockholm)
- **Environment:** `prod`
- **Project tag value:** `math-animate` (applied to all resources via `default_tags`)

## Directory Layout

```
infrastructure/
├── envs/
│   └── prod/
│       ├── main.tf    # The Terraform entrypoint: backend config + module wiring + outputs
│       ├── variables.tf
│       └── terraform.tfvars
├── modules/
│   ├── acm/           # ACM certificate for api.mathanimate.com + Cloudflare DNS validation records
│   ├── alb/           # ALB, target group (port 8000), HTTP/HTTPS listeners
│   ├── cloudflare/    # Cloudflare DNS record: api.mathanimate.com CNAME → ALB (proxied)
│   ├── ec2/           # Celery worker EC2 instance (AL2023), CW log group, userdata template
│   ├── ecs/           # ECS Fargate cluster, task definition, service (API container on :8000)
│   ├── elasticache/   # Redis 7.1 replication group (single node, cache.t3.micro)
│   ├── iam/           # ECS execution role, ECS task role, EC2 instance role + profile, GitHub Actions OIDC role
│   ├── networking/    # VPC, public/private subnets, IGW, NAT GW, route tables, 7 VPC endpoints
│   ├── rds/           # PostgreSQL 16, parameter group (pg_stat_statements), Secrets Manager password
│   ├── s3/            # Artifact bucket only (frontend moved to Cloudflare Pages)
│   ├── security_groups/ # ALB (Cloudflare IP-locked), ECS API, EC2 worker, RDS, Redis, VPC endpoints SGs
│   └── sqs/           # mathanimate-jobs queue + mathanimate-jobs-dlq, queue resource policies
└── scripts/           # Helper shell scripts (see below)
```

## Module Wiring (envs/prod/main.tf)

The `name_prefix` local (`mathanimate-${var.environment}`) is defined in `envs/prod/main.tf` and passed into every module.

This environment directory is the only supported Terraform entrypoint in this repository. The old root-level Terraform stub files were removed to avoid ambiguity.

Dependency order (simplified, Terraform resolves automatically):

```
s3 -> iam -> networking -> security_groups -> rds, elasticache, sqs, acm -> alb -> ecs, ec2_worker, cloudflare
```

Key cross-module output wiring:
- `iam` takes `artifact_bucket_name` from `module.s3`
- `networking` takes `endpoint_security_group_ids` from `module.security_groups`
- `sqs` takes `ecs_task_role_arn` and `ec2_worker_role_arn` from `module.iam`
- `ecs` takes `target_group_arn` from `module.alb`, role ARNs from `module.iam`, connection URLs from `module.rds` and `module.elasticache`
- `ec2_worker` takes `instance_profile_name` (not role ARN) from `module.iam`, connection URLs from `module.rds` and `module.elasticache`

## Common Commands

All commands run from `infrastructure/envs/prod/`:

```bash
# Initialise (first time or after backend change)
terraform init

# Preview changes against prod
terraform plan

# Apply
terraform apply

# Targeted apply (example)
terraform apply -target=module.ecs

# Destroy (careful — RDS has deletion_protection = false)
terraform destroy

# Show outputs
terraform output
terraform output -raw alb_dns_name
```

## Key Variables

Variables are declared in `envs/prod/variables.tf` and set in `terraform.tfvars`.

| Variable | Default | Notes |
|---|---|---|
| `aws_region` | `eu-north-1` | |
| `environment` | `prod` | Used in resource names and secret paths |
| `vpc_cidr` | `10.0.0.0/16` | |
| `availability_zones` | `["eu-north-1a","eu-north-1b"]` | Minimum 2 required |
| `db_instance_class` | `db.t3.micro` | |
| `db_name` | `mathanimate` | |
| `db_username` | `mathanimate` | |
| `cache_node_type` | `cache.t3.micro` | |
| `sqs_visibility_timeout` | `900` | Must exceed max Celery task runtime |
| `api_cpu` / `api_memory` | `512` / `1024` | ECS Fargate task |
| `api_desired_count` | `1` | Ignored by `terraform apply` after initial creation (ECS lifecycle ignores it) |
| `worker_instance_type` | `t3.medium` | |
| `worker_ami_id` | *(required)* | Amazon Linux 2023 AMI for eu-north-1 |
| `artifact_lifecycle_days` | `30` | |
| `image_uri` | *(required)* | Docker Hub URI; shared by ECS task definition and EC2 worker |
| `github_org` | *(required)* | GitHub org/user for OIDC trust condition |
| `github_repo` | *(required)* | GitHub repo name for OIDC trust condition |
| `cloudflare_api_token` | *(required, sensitive)* | Cloudflare API token — Terraform provider + wrangler |
| `cloudflare_zone_id` | *(required)* | Cloudflare zone ID for `mathanimate.com` |

Note: `terraform.tfvars` sets `github_org = "https://github.com/Alonpenker"` (full URL). The IAM OIDC trust condition interpolates this into `repo:{github_org}/{github_repo}:ref:refs/heads/main`. Using the full URL here would cause the condition to never match — the value should be just the username or org name (e.g. `Alonpenker`).

## Secrets Naming Pattern

All Secrets Manager secrets follow the path `mathanimate/{environment}/{name}`.

The ECS task uses `repositoryCredentials` with a single JSON blob secret looked up by name (no variable needed):
- `mathanimate/{env}/dockerhub-credentials` — JSON `{"username":"...","password":"..."}` — looked up via `data "aws_secretsmanager_secret"` in `modules/ecs/main.tf`

The EC2 worker user data (`userdata.sh.tpl`) reads the same `dockerhub-credentials` JSON blob and logs in via `docker login`.

Full secret inventory:

| Secret path | Managed by | Description |
|---|---|---|
| `mathanimate/prod/db-password` | Manual (pre-deploy) | RDS master password — read by Terraform (RDS resource), ECS (`DB_PASSWORD`), EC2 `.env` |
| `mathanimate/prod/x-api-key` | Manual (pre-deploy) | X-API-Key header value — gates REST API access |
| `mathanimate/prod/openai-api-key` | Manual (pre-deploy) | OpenAI API key for LLM plan and code generation calls |
| `mathanimate/prod/dockerhub-credentials` | Manual (AWS CLI) | JSON `{"username":"...","password":"..."}` — ECS `repositoryCredentials`, EC2 userdata docker login, CI image push |
| `mathanimate/prod/cloudflare-credentials` | Manual (AWS CLI) | JSON `{"api_token":"...","zone_id":"...","account_id":"..."}` — Terraform Cloudflare provider + zone_id, CI wrangler deploy |

GitHub Actions secrets (stored in the repo, not Secrets Manager):

| Secret | Used by |
|---|---|
| `AWS_ROLE_ARN` | All workflows — OIDC role assumption |

## Resource Naming Pattern

All resources use `mathanimate-${environment}-<resource>` as a prefix (e.g. `mathanimate-prod-ecs-execution-role`).

SQS queues are an exception — they use bare names: `mathanimate-jobs` and `mathanimate-jobs-dlq`. The IAM policies reference these queues by hardcoded ARN patterns rather than module outputs.

## IAM Roles Summary

| Role | Principal | Key permissions |
|---|---|---|
| `mathanimate-{env}-ecs-execution-role` | `ecs-tasks.amazonaws.com` | Pull images, write logs, read `mathanimate/{env}/*` secrets |
| `mathanimate-{env}-ecs-task-role` | `ecs-tasks.amazonaws.com` | S3 artifact r/w/delete/list, SQS send, Secrets Manager read/describe |
| `mathanimate-{env}-ec2-worker-role` | `ec2.amazonaws.com` | S3 artifact r/w/delete/list, SQS receive/delete/change-visibility, Secrets Manager read/describe, CW Logs write to `/mathanimate/*`, SSM core (AmazonSSMManagedInstanceCore) |
| `mathanimate-{env}-github-actions-deploy` | GitHub OIDC (main branch only) | ECS deploy, SSM send-command, IAM PassRole to ECS, Terraform state (S3 + DynamoDB), all actions in `aws_region` |

The GitHub OIDC trust uses `StringLike` for the `sub` claim (`repo:{org}/{repo}:ref:refs/heads/main`) and `StringEquals` for the `aud` claim (`sts.amazonaws.com`). The OIDC provider must be pre-created in the account — the module reads it via a `data "aws_iam_openid_connect_provider"` source.

## ECS Task Definition Details

The task definition injects environment variables at definition time:
- `ENVIRONMENT`, `AWS_REGION`, `BROKER_URL=sqs://`, `SQS_QUEUE_URL`, `STORAGE_BUCKET`, `STORAGE_ENDPOINT=s3.amazonaws.com`, `DATABASE_URL` (password-less template), `REDIS_URL`, `FRONTEND_URL`

Secrets injected via `valueFrom` (using secret name, not ARN — simpler and avoids the random ARN suffix):
- `X_API_KEY` ← `mathanimate/{env}/x-api-key`
- `DB_PASSWORD` ← `mathanimate/{env}/db-password`
- `OPENAI_API_KEY` ← `mathanimate/{env}/openai-api-key`

The `DATABASE_URL` template passed to ECS is password-free: `postgresql://{username}@{rds_address}:{port}/{db_name}`. The application reads `DB_PASSWORD` separately via the injected secret.

## EC2 Worker Details

- AMI: Amazon Linux 2023 (x86_64), `ami-0c02fb55956c7d316` in prod
- Instance type: `t3.medium`, placed in `private_subnet_ids[0]`
- Root volume: 50 GB gp3, encrypted, deleted on termination
- IMDSv2 enforced (`http_tokens = required`, `http_put_response_hop_limit = 1`)
- No inbound security group rules — managed exclusively via SSM Session Manager
- User data installs: Docker, AWS CLI v2, CloudWatch agent (`amazon-cloudwatch-agent`), SSM agent (`amazon-ssm-agent`)
- User data writes `/opt/mathanimate-worker/.env` (mode 600) and installs `celery-worker.service`
- The systemd service runs: `docker run --rm --name celery-worker --env-file /opt/mathanimate-worker/.env --volume /var/run/docker.sock:/var/run/docker.sock --volume /job:/job {image_uri} uv run celery -A app.workers.worker worker --loglevel=info`
- Terraform ignores `user_data` and `ami` changes post-provisioning (`lifecycle.ignore_changes`)
- GitHub Actions updates the worker by rebooting the EC2 instance via `infrastructure/scripts/deploy-worker.sh`; the `celery-worker.service` is enabled and starts automatically on boot
- CloudWatch agent ships `/var/log/user-data.log` and `/var/log/celery-worker.log` to log group `/mathanimate/ec2/worker`

## CloudWatch Log Groups

| Log group | Retention | Created by |
|---|---|---|
| `/mathanimate/ecs/api` | 3 days | `modules/ecs/main.tf` |
| `/mathanimate/ec2/worker` | 3 days | `modules/ec2/main.tf` |

## VPC Endpoints

Seven VPC endpoints are created by `modules/networking`:

| Type | Service |
|---|---|
| Gateway | `s3` — routes S3 traffic from private subnets, free of charge |
| Interface | `sqs` |
| Interface | `secretsmanager` |
| Interface | `logs` (CloudWatch Logs) |
| Interface | `ssm` |
| Interface | `ssmmessages` |
| Interface | `ec2messages` |

All interface endpoints use `private_dns_enabled = true` and are attached to the `vpc_endpoints` security group.

## ECS Service Lifecycle Behaviour

The ECS service has:
```hcl
lifecycle {
  ignore_changes = [task_definition, desired_count]
}
```

This means:
- Terraform will not update the task definition after initial creation. To deploy a new image via Terraform, you must force-apply a new value of `image_uri`.
- GitHub Actions deploys use `aws ecs update-service --force-new-deployment`, which restarts tasks using the task definition already registered — it does NOT register a new revision with the updated image URI.
- To change the image tag in production: re-run `terraform apply` with the updated `image_uri`, or register a new task definition revision manually.

## Pause Workflow (Partial Teardown)

The `pause.yml` GitHub Actions workflow destroys all metered resources via targeted `terraform destroy`:

Destroyed: `ecs`, `ec2_worker`, `alb`, `rds`, `elasticache`, `sqs`, `security_groups`, `networking`

Preserved: `iam`, `s3`, `cloudflare`, `acm`, Secrets Manager entries, Docker Hub images

To resume: run the `Terraform` workflow (manual dispatch) to re-apply infrastructure, then run the `Deploy` workflow (manual dispatch) to redeploy the application.

## Conventions

- All resources are tagged `Project = "math-animate"`, `Environment = var.environment`, `ManagedBy = "terraform"` via `default_tags` on the provider.
- Sensitive values (DB password, API keys, Docker Hub tokens) are never committed — managed via Secrets Manager.
- Each module is self-contained with `variables.tf` and `outputs.tf`.
- The `security_groups` module uses separate `aws_vpc_security_group_ingress_rule` / `aws_vpc_security_group_egress_rule` resources (not inline blocks) to avoid dependency cycles between security groups that reference each other.
- The `db-password` secret is created manually before `terraform apply` and is read (not managed) by Terraform. It is preserved through pause/destroy cycles.
- ALB `deregistration_delay = 30` (seconds) for fast rolling deploys.

## Scripts

| Script | Usage | Description |
|---|---|---|
| `build-and-push.sh` | `DOCKERHUB_USERNAME=<user> DOCKERHUB_TOKEN=<tok> ./build-and-push.sh` | Builds and pushes `:latest` tag for `linux/amd64` to Docker Hub |
| `deploy-worker.sh` | `./deploy-worker.sh` | Reboots the EC2 worker instance (found by `Project`/`Environment` tags) and waits for status checks to pass |
| `run-migrations.sh` | `./run-migrations.sh eu-north-1 mathanimate-prod-cluster` | Launches ECS one-off task that calls `init_db_pool()` + `init_db_tables()`; polls 300 s |
