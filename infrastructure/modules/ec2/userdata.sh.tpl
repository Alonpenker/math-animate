#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1
echo "[user-data] Starting worker provisioning — $(date -u)"

# 1. System packages: Docker (includes compose plugin), CloudWatch agent
dnf update -y
dnf install -y docker amazon-cloudwatch-agent unzip

systemctl enable --now docker
usermod -aG docker ec2-user

# 2. AWS CLI v2
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscli.zip
unzip -q /tmp/awscli.zip -d /tmp/
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscli.zip

# 3. CloudWatch agent config
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CWCONFIG'
{ "logs": { "logs_collected": { "files": { "collect_list": [
  { "file_path": "/var/log/user-data.log",
    "log_group_name": "${log_group_name}",
    "log_stream_name": "{instance_id}/user-data", "timezone": "UTC" }
] } } } }
CWCONFIG
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# 4. Create app directory and write docker-compose.yml inline
mkdir -p /opt/mathanimate
cat > /opt/mathanimate/docker-compose.yml << 'COMPOSE'
${docker_compose_content}
COMPOSE

# 5. Fetch secrets and authenticate to Docker Hub
get_secret() {
  aws secretsmanager get-secret-value --region "${aws_region}" \
    --secret-id "mathanimate/${environment}/$1" --query SecretString --output text
}

DOCKERHUB_USERNAME=$(get_secret "dockerhub-username")
DOCKERHUB_TOKEN=$(get_secret "dockerhub-token")
echo "$${DOCKERHUB_TOKEN}" | docker login --username "$${DOCKERHUB_USERNAME}" --password-stdin

# 6. Write .env for docker compose (OLLAMA_BASE_URL is set in the compose file directly)
cat > /opt/mathanimate/.env << EOF
ENVIRONMENT=${environment}
AWS_REGION=${aws_region}
DATABASE_URL=${database_url}
REDIS_URL=${redis_url}
BROKER_URL=sqs://
SQS_QUEUE_URL=${sqs_queue_url}
STORAGE_ENDPOINT=s3.amazonaws.com
STORAGE_BUCKET=${artifact_bucket_name}
STORAGE_ACCESS_KEY=$(get_secret "storage-access-key")
STORAGE_SECRET_KEY=$(get_secret "storage-secret-key")
API_KEY=$(get_secret "api-key")
FRONTEND_URL=
WORKER_IMAGE_URI=${worker_image_uri}
EOF
chmod 600 /opt/mathanimate/.env

# 7. Systemd unit to manage docker compose (handles reboots)
cat > /etc/systemd/system/mathanimate.service << UNIT
[Unit]
Description=MathAnimate Worker Stack
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/mathanimate
ExecStartPre=/bin/bash -c 'DOCKERHUB_USERNAME=$$(aws secretsmanager get-secret-value --region ${aws_region} --secret-id mathanimate/${environment}/dockerhub-username --query SecretString --output text) && \
  DOCKERHUB_TOKEN=$$(aws secretsmanager get-secret-value --region ${aws_region} --secret-id mathanimate/${environment}/dockerhub-token --query SecretString --output text) && \
  echo "$$DOCKERHUB_TOKEN" | docker login --username "$$DOCKERHUB_USERNAME" --password-stdin'
ExecStart=/usr/bin/docker compose up -d --pull always
ExecStop=/usr/bin/docker compose down
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable mathanimate
systemctl start mathanimate

echo "[user-data] Provisioning complete — $(date -u)"
