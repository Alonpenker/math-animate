#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.frontend.yml -f docker-compose.vps.yml"

WIPE_DB=false
WIPE_MINIO=false

for arg in "$@"; do
  case "$arg" in
    --db)    WIPE_DB=true ;;
    --minio) WIPE_MINIO=true ;;
  esac
done

if [[ "$WIPE_DB" == false && "$WIPE_MINIO" == false ]]; then
  WIPE_DB=true
  WIPE_MINIO=true
fi

echo "=== Stopping stack ==="
$COMPOSE down

[[ "$WIPE_DB"    == true ]] && { echo "=== Removing postgres_data ==="; docker volume rm mathanimate-backend_postgres_data || true; }
[[ "$WIPE_MINIO" == true ]] && { echo "=== Removing minio_data ===";   docker volume rm mathanimate-backend_minio_data    || true; }

echo "=== Restarting stack ==="
$COMPOSE up -d
