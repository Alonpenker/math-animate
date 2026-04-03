#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

# Load backend env
set -a
# shellcheck source=../backend/.env
source <(sed 's/\r//' backend/.env)
set +a

docker compose --project-directory . \
  -f backend/docker-compose.yml \
  -f docker-compose.vps.yml \
  up -d --build
