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
worker_ami_id        = "ami-0f77cdd9f61b7735e"

# ── S3 ─────────────────────────────────────────────────────────────────────────
artifact_lifecycle_days = 30

# ── Container Image ────────────────────────────────────────────────────────────
# Populated after running build-and-push.sh; overridden by GitHub Actions on
# each deploy. API and Worker share the same image (startup command differs).
image_uri = "alonpenker/math-animate-backend:latest"

# ── CORS / Frontend URL ────────────────────────────────────────────────────────
frontend_url = "https://mathanimate.com"
