#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

docker compose \
  -f docker-compose.yml \
  -f docker-compose.frontend.yml \
  -f docker-compose.vps.yml \
  down
