#!/usr/bin/env bash
# deploy-worker.sh — Reboot the EC2 worker so it picks up the latest image on startup.
#
# Usage: ./deploy-worker.sh
#
# Requires AWS credentials to be configured in the environment (e.g. via OIDC in CI).

set -euo pipefail

REGION="eu-north-1"

# ── Locate the running worker instance ────────────────────────────────────────
INSTANCE_ID=$(aws ec2 describe-instances \
  --region "$REGION" \
  --filters \
    "Name=tag:Project,Values=math-animate" \
    "Name=tag:Environment,Values=prod" \
    "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text)

if [[ -z "$INSTANCE_ID" || "$INSTANCE_ID" == "None" ]]; then
  echo "Worker instance not found — skipping."
  exit 0
fi

echo "==> Rebooting instance: $INSTANCE_ID"
aws ec2 reboot-instances --instance-ids "$INSTANCE_ID" --region "$REGION"

echo "==> Waiting for instance to pass status checks..."
aws ec2 wait instance-status-ok --instance-ids "$INSTANCE_ID" --region "$REGION"

echo "==> Worker instance is back up."
