#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

# Load backend env so compose can interpolate ${STORAGE_ACCESS_KEY} etc. for MinIO
set -a
# shellcheck source=../backend/.env
source <(sed 's/\r//' backend/.env)
set +a

docker compose \
  -f docker-compose.yml \
  -f docker-compose.frontend.yml \
  -f docker-compose.vps.yml \
  up -d --build
