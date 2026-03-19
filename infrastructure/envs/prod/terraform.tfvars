# ── Region & Environment ───────────────────────────────────────────────────────
aws_region  = "eu-north-1"
environment = "prod"

# ── Networking ─────────────────────────────────────────────────────────────────
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["eu-north-1a", "eu-north-1b"]

# ── Database ───────────────────────────────────────────────────────────────────
db_instance_class = "db.t3.micro"
db_name           = "mathanimate"
db_username       = "mathanimate"

# ── ElastiCache ────────────────────────────────────────────────────────────────
cache_node_type = "cache.t3.micro"

# ── SQS ────────────────────────────────────────────────────────────────────────
sqs_visibility_timeout = 900

# ── ECS ────────────────────────────────────────────────────────────────────────
api_cpu           = 512
api_memory        = 1024
api_desired_count = 1

# ── EC2 Worker ─────────────────────────────────────────────────────────────────
worker_instance_type = "t3.medium"
# worker_ami_id — set to latest Amazon Linux 2023 AMI for eu-north-1
# Run: aws ec2 describe-images --owners amazon \
#        --filters "Name=name,Values=al2023-ami-2023*" "Name=architecture,Values=x86_64" \
#        --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text
worker_ami_id = "ami-0c02fb55956c7d316"

# ── S3 ─────────────────────────────────────────────────────────────────────────
artifact_lifecycle_days = 30

# ── ALB (leave empty for HTTP-only demo; set ACM ARN to enable HTTPS) ──────────
alb_certificate_arn = ""

# ── Container Image ────────────────────────────────────────────────────────────
# Populated after running build-and-push.sh; overridden by GitHub Actions on
# each deploy. API and Worker share the same image (startup command differs).
image_uri = "alonpenker/math-animate-backend:latest"

# ── Docker Hub ─────────────────────────────────────────────────────────────────
# ARN of the Secrets Manager secret containing Docker Hub credentials.
# Create with: aws secretsmanager create-secret --name mathanimate/prod/dockerhub-credentials \
#   --secret-string '{"username":"youruser","password":"your-access-token"}'
dockerhub_credentials_secret_arn = "arn:aws:secretsmanager:eu-north-1:346971617751:secret:mathanimate/prod/dockerhub-credentials-Qd9dYj"

# ── GitHub OIDC ────────────────────────────────────────────────────────────────
github_org  = "https://github.com/Alonpenker"
github_repo = "math-animate"
