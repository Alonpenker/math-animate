#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1
echo "[user-data] Starting worker provisioning — $(date -u)"

# 1. System packages: Docker, docker-compose plugin, CloudWatch agent, jq
dnf update -y
dnf install -y docker amazon-cloudwatch-agent jq unzip

# Docker Compose v2 plugin (not available as an AL2023 dnf package)
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL "https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

systemctl enable --now docker
usermod -aG docker ec2-user

# 2. AWS CLI v2
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscli.zip
unzip -q /tmp/awscli.zip -d /tmp/
/tmp/aws/install
rm -rf /tmp/aws /tmp/awscli.zip

# 3. CloudWatch agent config — ships user-data bootstrap log and the worker log
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CWCONFIG'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/user-data",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/celery-worker.log",
            "log_group_name": "${log_group_name}",
            "log_stream_name": "{instance_id}/celery",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
CWCONFIG

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# 4. Fetch Docker Hub credentials and log in (credentials cached on root's docker config
#    for the lifetime of this instance — docker compose up re-uses them on restart)
get_secret() {
  aws secretsmanager get-secret-value --region "${aws_region}" \
    --secret-id "mathanimate/${environment}/$1" --query SecretString --output text
}

CREDS=$(get_secret "dockerhub-credentials")
DOCKERHUB_USERNAME=$(echo "$CREDS" | jq -r '.username')
DOCKERHUB_TOKEN=$(echo "$CREDS" | jq -r '.password')
echo "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin

# 5. Write .env for the worker container
mkdir -p /opt/mathanimate-worker
chmod 700 /opt/mathanimate-worker

cat > /opt/mathanimate-worker/.env << EOF
ENVIRONMENT=${environment}
AWS_REGION=${aws_region}
FRONTEND_URL=${frontend_url}
DATABASE_URL=${database_url}
REDIS_URL=${redis_url}
BROKER_URL=sqs://
SQS_QUEUE_URL=${sqs_queue_url}
STORAGE_ENDPOINT=s3.amazonaws.com
STORAGE_BUCKET=${artifact_bucket_name}
STORAGE_ACCESS_KEY=${storage_access_key}
STORAGE_SECRET_KEY=${storage_secret_key}
X_API_KEY=$(get_secret "x-api-key")
OPENAI_API_KEY=$(get_secret "openai-api-key")
EOF
chmod 600 /opt/mathanimate-worker/.env

# 6. Download docker-compose.yml from S3 (uploaded by Terraform apply)
#    and inject the worker image URI.
aws s3 cp "s3://${artifact_bucket_name}/${compose_s3_key}" \
  /opt/mathanimate-worker/docker-compose.yml --region "${aws_region}"

# \$${WORKER_IMAGE_URI} — Terraform converts $$ -> $, so bash sees $${WORKER_IMAGE_URI}
# as the literal sed pattern (double-quoted string, \$ prevents shell expansion).
WORKER_IMAGE="${worker_image_uri}"
sed -i "s|image: \$${WORKER_IMAGE_URI}|image: $WORKER_IMAGE|" \
  /opt/mathanimate-worker/docker-compose.yml

# 7. Systemd unit — runs all three services via docker compose, restarts on failure
cat > /etc/systemd/system/celery-worker.service << UNIT
[Unit]
Description=MathAnimate Worker Stack (ollama + docker-daemon + celery)
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=simple
Restart=on-failure
RestartSec=15
WorkingDirectory=/opt/mathanimate-worker
StandardOutput=append:/var/log/celery-worker.log
StandardError=append:/var/log/celery-worker.log

ExecStart=/usr/bin/docker compose -f /opt/mathanimate-worker/docker-compose.yml up --abort-on-container-exit --remove-orphans
ExecStop=/usr/bin/docker compose -f /opt/mathanimate-worker/docker-compose.yml down

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable celery-worker
systemctl start celery-worker

# 8. Health-check script — polls until all three services are ready,
#    then publishes CloudWatch custom metrics (1 = healthy, 0 = unhealthy)
cat > /opt/mathanimate-worker/healthcheck.sh << 'HEALTHCHECK'
#!/bin/bash
REGION="${aws_region}"
NAMESPACE="MathAnimate/Worker"
TOKEN=$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -sf -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

put_metric() {
  local name=$1 value=$2
  aws cloudwatch put-metric-data \
    --region "$REGION" \
    --namespace "$NAMESPACE" \
    --metric-name "$name" \
    --value "$value" \
    --dimensions "InstanceId=$INSTANCE_ID"
}

# Wait up to 20 minutes for everything to be ready
for i in $(seq 1 40); do
  sleep 30
  echo "[healthcheck] Attempt $i — $(date -u)"

  # 1. Docker daemon running + manim image pulled (image lives inside the DinD container)
  if docker info >/dev/null 2>&1 && docker exec mathanimate-worker-docker-daemon-1 docker image inspect "manimcommunity/manim:v0.19.2" >/dev/null 2>&1; then
    put_metric "DockerDaemonReady" 1
    DOCKER_OK=1
  else
    put_metric "DockerDaemonReady" 0
    DOCKER_OK=0
  fi

  # 2. Ollama running + nomic-embed-text model downloaded
  if docker exec mathanimate-worker-ollama-1 ollama list 2>/dev/null | grep -q "nomic-embed-text"; then
    put_metric "OllamaModelReady" 1
    OLLAMA_OK=1
  else
    put_metric "OllamaModelReady" 0
    OLLAMA_OK=0
  fi

  # 3. Celery worker container running
  if docker compose -f /opt/mathanimate-worker/docker-compose.yml ps --status running 2>/dev/null | grep -q "worker-worker"; then
    put_metric "CeleryWorkerReady" 1
    CELERY_OK=1
  else
    put_metric "CeleryWorkerReady" 0
    CELERY_OK=0
  fi

  echo "[healthcheck] docker=$DOCKER_OK ollama=$OLLAMA_OK celery=$CELERY_OK"

  if [ "$DOCKER_OK" = "1" ] && [ "$OLLAMA_OK" = "1" ] && [ "$CELERY_OK" = "1" ]; then
    echo "[healthcheck] All services healthy — worker ready"
    exit 0
  fi
done

echo "[healthcheck] Timed out waiting for services"
exit 1
HEALTHCHECK
chmod +x /opt/mathanimate-worker/healthcheck.sh

# Run healthcheck in background so it doesn't block userdata
nohup /opt/mathanimate-worker/healthcheck.sh >> /var/log/celery-worker.log 2>&1 &

echo "[user-data] Provisioning complete — $(date -u)"
