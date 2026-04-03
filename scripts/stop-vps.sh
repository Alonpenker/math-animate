#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

docker compose --project-directory . \
  -f backend/docker-compose.yml \
  -f docker-compose.vps.yml \
  down
