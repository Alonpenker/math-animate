# Infrastructure — CLAUDE.md

Terraform infrastructure for the **math-animate** project, targeting AWS.

## Stack

- **IaC:** Terraform >= 1.6.0, AWS provider ~5.0
- **Remote state:** S3 bucket `math-animate-tf-state`, DynamoDB lock table `math-animate-tf-locks`
- **Default region:** `eu-north-1` (Stockholm)
- **Environment:** `prod`

## Directory Layout

```
infrastructure/
├── main.tf            # Terraform + provider + backend config
├── variables.tf       # All input variables
├── outputs.tf         # Root outputs
├── envs/prod/         # Prod tfvars
├── modules/
│   ├── alb/           # Application Load Balancer
│   ├── ec2/           # Celery worker EC2 instance
│   ├── ecs/           # ECS Fargate API service
│   ├── elasticache/   # Redis (ElastiCache)
│   ├── iam/           # IAM roles & policies
│   ├── networking/    # VPC, subnets, routing
│   ├── rds/           # PostgreSQL (RDS)
│   ├── s3/            # Artifact bucket
│   ├── security_groups/
│   └── sqs/           # Task queue
└── scripts/           # Helper shell scripts
```

## Common Commands

```bash
# Initialise (first time or after backend change)
terraform init

# Preview changes against prod
terraform plan -var-file=envs/prod/terraform.tfvars

# Apply
terraform apply -var-file=envs/prod/terraform.tfvars

# Destroy (careful!)
terraform destroy -var-file=envs/prod/terraform.tfvars
```

## Key Variables

| Variable | Default | Notes |
|---|---|---|
| `aws_region` | `eu-north-1` | |
| `environment` | `prod` | |
| `worker_instance_type` | `t3.medium` | EC2 Celery worker |
| `api_cpu` / `api_memory` | `512` / `1024` | ECS Fargate task |
| `frontend_url` | *(required)* | Used for CORS |
| `ollama_base_url` | *(required)* | Ollama LLM endpoint |
| `github_org` / `github_repo` | *(required)* | OIDC trust for CI |

## Conventions

- All resources are tagged with `Project = "math-animate"`, `Environment`, and `ManagedBy = "terraform"` via `default_tags`.
- Sensitive values (DB password, secrets) are **never** committed — supply via tfvars or AWS Secrets Manager.
- Each module is self-contained; root `main.tf` wires modules together.
