terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "mathanimate-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "eu-north-1"
    dynamodb_table = "mathanimate-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "math-animate"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "cloudflare" {
  api_token = local.cloudflare_creds["api_token"]
}

data "aws_secretsmanager_secret_version" "cloudflare" {
  secret_id = "mathanimate/${var.environment}/cloudflare-credentials"
}

data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "mathanimate/${var.environment}/db-password"
}

locals {
  name_prefix        = "mathanimate-${var.environment}"
  cloudflare_creds   = jsondecode(data.aws_secretsmanager_secret_version.cloudflare.secret_string)
  cloudflare_zone_id = local.cloudflare_creds["zone_id"]
  database_url       = "postgresql://${var.db_username}:${data.aws_secretsmanager_secret_version.db_password.secret_string}@${module.rds.address}:${module.rds.port}/${var.db_name}"

  cloudflare_ipv4_cidrs = [
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "108.162.192.0/18",
    "131.0.72.0/22",
    "141.101.64.0/18",
    "162.158.0.0/15",
    "172.64.0.0/13",
    "173.245.48.0/20",
    "188.114.96.0/20",
    "190.93.240.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
  ]
}

data "aws_caller_identity" "current" {}

# ── S3 Buckets ─────────────────────────────────────────────────────────────────
module "s3" {
  source = "../../modules/s3"

  environment    = var.environment
  lifecycle_days = var.artifact_lifecycle_days
}

# ── IAM ────────────────────────────────────────────────────────────────────────
module "iam" {
  source = "../../modules/iam"

  name_prefix          = local.name_prefix
  aws_region           = var.aws_region
  aws_account_id       = data.aws_caller_identity.current.account_id
  environment          = var.environment
  artifact_bucket_name = module.s3.artifact_bucket_name
}

# ── Networking: VPC, subnets, route tables, S3 gateway endpoint ──────

module "networking" {
  source = "../../modules/networking"

  name_prefix                 = local.name_prefix
  aws_region                  = var.aws_region
  vpc_cidr                    = var.vpc_cidr
  availability_zones          = var.availability_zones
  endpoint_security_group_ids = [module.security_groups.vpc_endpoints_sg_id]
}

# ── Security Groups ─────────────
module "security_groups" {
  source = "../../modules/security_groups"

  name_prefix           = local.name_prefix
  vpc_id                = module.networking.vpc_id
  vpc_cidr              = var.vpc_cidr
  allowed_ingress_cidrs = local.cloudflare_ipv4_cidrs
}

# ── Data Layer ─────────────────────────────────────────────────────────────────
module "rds" {
  source = "../../modules/rds"

  name_prefix             = local.name_prefix
  environment             = var.environment
  private_subnet_ids = module.networking.private_subnet_ids
  rds_sg_id          = module.security_groups.rds_sg_id
  instance_class          = var.db_instance_class
  db_name                 = var.db_name
  db_username             = var.db_username
}

module "elasticache" {
  source = "../../modules/elasticache"

  name_prefix             = local.name_prefix
  private_subnet_ids = module.networking.private_subnet_ids
  redis_sg_id        = module.security_groups.redis_sg_id
  node_type               = var.cache_node_type
}

module "sqs" {
  source = "../../modules/sqs"

  visibility_timeout  = var.sqs_visibility_timeout
  ecs_task_role_arn   = module.iam.ecs_task_role_arn
  ec2_worker_role_arn = module.iam.ec2_worker_role_arn
}

# ── ACM Certificate ─────────────────────────────────────────────────────────────
module "acm" {
  source = "../../modules/acm"

  zone_id = local.cloudflare_zone_id
}

# ── Compute ────────────────────────────────────────────────────────────────────
module "alb" {
  source = "../../modules/alb"

  name_prefix       = local.name_prefix
  vpc_id            = module.networking.vpc_id
  alb_sg_id         = module.security_groups.alb_sg_id
  public_subnet_ids = module.networking.public_subnet_ids
  certificate_arn   = module.acm.certificate_arn
}

module "ecs" {
  source = "../../modules/ecs"

  name_prefix            = local.name_prefix
  environment            = var.environment
  private_subnet_ids = module.networking.private_subnet_ids
  ecs_api_sg_id      = module.security_groups.ecs_api_sg_id
  target_group_arn       = module.alb.target_group_arn
  ecs_execution_role_arn = module.iam.ecs_execution_role_arn
  ecs_task_role_arn      = module.iam.ecs_task_role_arn
  image_uri                        = var.image_uri
  cpu                    = var.api_cpu
  memory                 = var.api_memory
  desired_count          = var.api_desired_count
  sqs_queue_url          = module.sqs.queue_url
  artifact_bucket_name   = module.s3.artifact_bucket_name
  database_url           = local.database_url
  redis_url              = module.elasticache.redis_url
  frontend_url           = var.frontend_url
  storage_access_key     = module.iam.storage_access_key_id
  storage_secret_key     = module.iam.storage_secret_access_key
}

module "ec2_worker" {
  source = "../../modules/ec2"

  name_prefix            = local.name_prefix
  environment            = var.environment
  ami_id                 = var.worker_ami_id
  instance_type          = var.worker_instance_type
  private_subnet_ids     = module.networking.private_subnet_ids
  worker_sg_id           = module.security_groups.ec2_worker_sg_id
  instance_profile_name  = module.iam.ec2_worker_instance_profile_name
  image_uri              = var.image_uri
  artifact_bucket_name   = module.s3.artifact_bucket_name
  sqs_queue_url          = module.sqs.queue_url
  database_url           = local.database_url
  redis_url              = module.elasticache.redis_url
  frontend_url           = var.frontend_url
  storage_access_key     = module.iam.storage_access_key_id
  storage_secret_key     = module.iam.storage_secret_access_key
}

# ── Cloudflare DNS ─────────────────────────────────────────────────────────────
module "cloudflare" {
  source = "../../modules/cloudflare"

  zone_id      = local.cloudflare_zone_id
  alb_dns_name = module.alb.alb_dns_name
}

# ── Outputs ────────────────────────────────────────────────────────────────────
output "alb_dns_name" {
  description = "ALB DNS name — API base URL"
  value       = module.alb.alb_dns_name
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS API service name"
  value       = module.ecs.service_name
}

output "ec2_worker_instance_id" {
  description = "EC2 worker instance ID"
  value       = module.ec2_worker.instance_id
}

output "s3_artifact_bucket" {
  description = "Artifact S3 bucket name"
  value       = module.s3.artifact_bucket_name
}

output "sqs_queue_url" {
  description = "SQS main queue URL"
  value       = module.sqs.queue_url
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = module.elasticache.primary_endpoint
}

output "github_actions_role_arn" {
  description = "GitHub Actions OIDC deploy role ARN — set as AWS_ROLE_ARN secret"
  value       = module.iam.github_actions_role_arn
}
