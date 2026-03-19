#!/usr/bin/env bash
# worker-userdata.sh — Standalone version of the EC2 worker user data script
#
# This script is the human-readable, standalone form of the EC2 user data that
# bootstraps the Celery worker. The Terraform module renders its own version via
# the userdata.sh.tpl template. This copy is provided as a reference and can be
# used to manually re-provision a worker instance if needed.
#
# Usage (on the EC2 instance as root):
#   AWS_REGION=eu-north-1 \
#   ENVIRONMENT=prod \
#   WORKER_IMAGE_URI=youruser/math-animate-worker:latest \
#   ARTIFACT_BUCKET=mathanimate-artifacts-prod \
#   SQS_QUEUE_URL=https://sqs.eu-north-1.amazonaws.com/123456789012/mathanimate-jobs \
#   DATABASE_URL=postgresql://mathanimate:password@rds-endpoint:5432/mathanimate \
#   REDIS_URL=redis://elasticache-endpoint:6379/0 \
#   OLLAMA_BASE_URL=http://10.0.2.100:11434 \
#   bash worker-userdata.sh

set -euo pipefail

# ── Required environment variables ────────────────────────────────────────────
: "${AWS_REGION:?AWS_REGION is required}"
: "${ENVIRONMENT:?ENVIRONMENT is required}"
: "${WORKER_IMAGE_URI:?WORKER_IMAGE_URI is required}"
: "${ARTIFACT_BUCKET:?ARTIFACT_BUCKET is required}"
: "${SQS_QUEUE_URL:?SQS_QUEUE_URL is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${REDIS_URL:?REDIS_URL is required}"
: "${OLLAMA_BASE_URL:?OLLAMA_BASE_URL is required}"

# ── Logging ────────────────────────────────────────────────────────────────────
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1
echo "[worker-userdata] Starting worker provisioning — $(date -u)"

# ── 1. System updates ──────────────────────────────────────────────────────────
echo "[worker-userdata] Updating system packages..."
dnf update -y

# ── 2. Install Docker Engine ───────────────────────────────────────────────────
echo "[worker-userdata] Installing Docker..."
dnf install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user
echo "[worker-userdata] Docker installed and started."

# ── 3. Install AWS CLI v2 ──────────────────────────────────────────────────────
echo "[worker-userdata] Installing AWS CLI..."
dnf install -y unzip curl
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscli.zip
unzip -q /tmp/awscli.zip -d /tmp/
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscli.zip
echo "[worker-userdata] AWS CLI installed."

# ── 4. Install CloudWatch agent ────────────────────────────────────────────────
echo "[worker-userdata] Installing CloudWatch agent..."
dnf install -y amazon-cloudwatch-agent

cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CWCONFIG'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/celery-worker.log",
            "log_group_name": "/mathanimate/ec2/worker",
            "log_stream_name": "{instance_id}/celery",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/mathanimate/ec2/worker",
            "log_stream_name": "{instance_id}/user-data",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
CWCONFIG

systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# ── 5. Authenticate Docker to Docker Hub ──────────────────────────────────────
echo "[worker-userdata] Authenticating to Docker Hub..."
DOCKERHUB_USERNAME=$(aws secretsmanager get-secret-value \
  --region "${AWS_REGION}" \
  --secret-id "mathanimate/${ENVIRONMENT}/dockerhub-username" \
  --query SecretString --output text)
DOCKERHUB_TOKEN=$(aws secretsmanager get-secret-value \
  --region "${AWS_REGION}" \
  --secret-id "mathanimate/${ENVIRONMENT}/dockerhub-token" \
  --query SecretString --output text)
echo "${DOCKERHUB_TOKEN}" | docker login --username "${DOCKERHUB_USERNAME}" --password-stdin

# ── 6. Pull Docker images ──────────────────────────────────────────────────────
echo "[worker-userdata] Pulling Manim renderer image (manimcommunity/manim:v0.19.2)..."
docker pull "manimcommunity/manim:v0.19.2"
echo "[worker-userdata] Manim renderer image pulled."

echo "[worker-userdata] Pulling worker image (${WORKER_IMAGE_URI})..."
docker pull "${WORKER_IMAGE_URI}"
echo "[worker-userdata] Worker image pulled."

# ── 7. Fetch secrets from Secrets Manager and write .env ──────────────────────
echo "[worker-userdata] Fetching application secrets..."
mkdir -p /opt/mathanimate-worker
chmod 700 /opt/mathanimate-worker

get_secret() {
  aws secretsmanager get-secret-value \
    --region "${AWS_REGION}" \
    --secret-id "mathanimate/${ENVIRONMENT}/$1" \
    --query SecretString \
    --output text
}

API_KEY=$(get_secret "api-key")
STORAGE_ACCESS_KEY=$(get_secret "storage-access-key")
STORAGE_SECRET_KEY=$(get_secret "storage-secret-key")

cat > /opt/mathanimate-worker/.env << EOF
ENVIRONMENT=${ENVIRONMENT}
AWS_REGION=${AWS_REGION}
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
BROKER_URL=sqs://
SQS_QUEUE_URL=${SQS_QUEUE_URL}
STORAGE_ENDPOINT=s3.amazonaws.com
STORAGE_BUCKET=${ARTIFACT_BUCKET}
STORAGE_ACCESS_KEY=${STORAGE_ACCESS_KEY}
STORAGE_SECRET_KEY=${STORAGE_SECRET_KEY}
OLLAMA_BASE_URL=${OLLAMA_BASE_URL}
API_KEY=${API_KEY}
FRONTEND_URL=
EOF

chmod 600 /opt/mathanimate-worker/.env
echo "[worker-userdata] .env written to /opt/mathanimate-worker/.env"

# ── 8. Create systemd service for Celery worker ───────────────────────────────
echo "[worker-userdata] Creating celery-worker systemd service..."

cat > /etc/systemd/system/celery-worker.service << UNIT
[Unit]
Description=MathAnimate Celery Worker
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=simple
User=ec2-user
Group=docker
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/celery-worker.log
StandardError=append:/var/log/celery-worker.log

ExecStartPre=/bin/bash -c 'DOCKERHUB_USERNAME=$$(aws secretsmanager get-secret-value --region ${AWS_REGION} --secret-id mathanimate/${ENVIRONMENT}/dockerhub-username --query SecretString --output text) && DOCKERHUB_TOKEN=$$(aws secretsmanager get-secret-value --region ${AWS_REGION} --secret-id mathanimate/${ENVIRONMENT}/dockerhub-token --query SecretString --output text) && echo "$$DOCKERHUB_TOKEN" | docker login --username "$$DOCKERHUB_USERNAME" --password-stdin'
ExecStartPre=/usr/bin/docker pull ${WORKER_IMAGE_URI}

ExecStart=/usr/bin/docker run --rm \
  --name celery-worker \
  --env-file /opt/mathanimate-worker/.env \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  --volume /job:/job \
  ${WORKER_IMAGE_URI} \
  uv run celery -A app.workers.worker worker --loglevel=info

ExecStop=/usr/bin/docker stop celery-worker

[Install]
WantedBy=multi-user.target
UNIT

# ── 9. Enable and start the worker ────────────────────────────────────────────
systemctl daemon-reload
systemctl enable celery-worker
systemctl start celery-worker

echo "[worker-userdata] Celery worker service started."
echo "[worker-userdata] Provisioning complete — $(date -u)"
echo ""
echo "To check worker status:"
echo "  systemctl status celery-worker"
echo "  journalctl -u celery-worker -f"
echo "  tail -f /var/log/celery-worker.log"
