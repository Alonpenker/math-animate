#!/usr/bin/env bash
# run-migrations.sh — Run DB schema migrations and pgvector setup via ECS one-off task
#
# This script launches an ECS one-off task using the API image with an overridden
# command. The task runs the migration SQL (including CREATE EXTENSION IF NOT EXISTS
# vector) and then exits. The script waits for the task to complete and reports
# success or failure.
#
# Usage: ./run-migrations.sh <region> <cluster-name>
#
# Example:
#   ./run-migrations.sh eu-north-1 mathanimate-prod-cluster
#
# Prerequisites:
#   - Terraform has been applied (ECS cluster, task definition, subnets, and SGs exist)
#   - RDS is reachable from the private app subnets
#   - Docker Hub image has been pushed

set -euo pipefail

# ── Argument validation ────────────────────────────────────────────────────────
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <region> <cluster-name>" >&2
  exit 1
fi

readonly ENV="prod"
REGION="$1"
CLUSTER="$2"

echo "==> Running DB migrations"
echo "    region:  ${REGION}"
echo "    cluster: ${CLUSTER}"
echo ""

# ── Resolve ECS task definition and network config from existing service ───────
SERVICE_NAME="mathanimate-${ENV}-api"

echo "==> Resolving task definition from service ${SERVICE_NAME}..."
TASK_DEF_ARN=$(aws ecs describe-services \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --services "${SERVICE_NAME}" \
  --query "services[0].taskDefinition" \
  --output text)

echo "    Task definition: ${TASK_DEF_ARN}"

# Extract network config from the running service
NETWORK_CONFIG=$(aws ecs describe-services \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --services "${SERVICE_NAME}" \
  --query "services[0].networkConfiguration" \
  --output json)

echo "    Network config resolved."

# ── Fetch database connection details from Secrets Manager ───────────────────
echo "==> Fetching DB credentials..."
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --region "${REGION}" \
  --secret-id "mathanimate/${ENV}/db-password" \
  --query SecretString \
  --output text)

# Get database URL from task definition environment
DATABASE_URL=$(aws ecs describe-task-definition \
  --region "${REGION}" \
  --task-definition "${TASK_DEF_ARN}" \
  --query "taskDefinition.containerDefinitions[0].environment[?name=='DATABASE_URL'].value" \
  --output text)

# Replace placeholder password in DATABASE_URL if needed (the actual DB password
# is stored in Secrets Manager; the task definition holds the URL template)
echo "    Database URL resolved from task definition."

# ── Run migrations as an ECS one-off task ─────────────────────────────────────
# The migration command enables pgvector and creates/updates the application schema.
# This uses the same API image so all the DB init code is available.
MIGRATION_COMMAND='["sh", "-c", "cd /app && uv run python -c \"from app.dependencies.db import init_db_pool, init_db_tables; init_db_pool(); init_db_tables(); print('"'"'Migrations complete'"'"')\""]'

echo "==> Launching ECS migration task..."
TASK_ARN=$(aws ecs run-task \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --task-definition "${TASK_DEF_ARN}" \
  --launch-type FARGATE \
  --network-configuration "${NETWORK_CONFIG}" \
  --overrides "{
    \"containerOverrides\": [{
      \"name\": \"api\",
      \"command\": [\"sh\", \"-c\",
        \"uv run python -c 'from app.dependencies.db import init_db_pool, init_db_tables; init_db_pool(); init_db_tables(); print(\\\"Migrations complete\\\")'\"]
    }]
  }" \
  --query "tasks[0].taskArn" \
  --output text)

if [[ -z "${TASK_ARN}" || "${TASK_ARN}" == "None" ]]; then
  echo "ERROR: Failed to launch ECS migration task" >&2
  exit 1
fi

echo "    Task ARN: ${TASK_ARN}"
echo ""
echo "==> Waiting for migration task to complete (timeout: 300s)..."

# Poll task status every 10 seconds for up to 5 minutes
MAX_WAIT=300
ELAPSED=0
while [[ ${ELAPSED} -lt ${MAX_WAIT} ]]; do
  TASK_STATUS=$(aws ecs describe-tasks \
    --region "${REGION}" \
    --cluster "${CLUSTER}" \
    --tasks "${TASK_ARN}" \
    --query "tasks[0].lastStatus" \
    --output text 2>/dev/null || echo "UNKNOWN")

  echo "    Status: ${TASK_STATUS} (${ELAPSED}s elapsed)"

  if [[ "${TASK_STATUS}" == "STOPPED" ]]; then
    break
  fi

  sleep 10
  ELAPSED=$((ELAPSED + 10))
done

if [[ "${TASK_STATUS}" != "STOPPED" ]]; then
  echo "ERROR: Migration task did not complete within ${MAX_WAIT}s" >&2
  exit 1
fi

# Check exit code
EXIT_CODE=$(aws ecs describe-tasks \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --tasks "${TASK_ARN}" \
  --query "tasks[0].containers[0].exitCode" \
  --output text)

STOP_REASON=$(aws ecs describe-tasks \
  --region "${REGION}" \
  --cluster "${CLUSTER}" \
  --tasks "${TASK_ARN}" \
  --query "tasks[0].stoppedReason" \
  --output text 2>/dev/null || echo "")

echo ""
echo "    Exit code:   ${EXIT_CODE}"
echo "    Stop reason: ${STOP_REASON}"

if [[ "${EXIT_CODE}" != "0" ]]; then
  echo ""
  echo "ERROR: Migration task failed with exit code ${EXIT_CODE}" >&2
  echo "       Check CloudWatch Logs at /mathanimate/ecs/api for details." >&2
  exit 1
fi

echo ""
echo "==> Migrations completed successfully."
