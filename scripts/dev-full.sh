#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

# Full stack, frontend (nginx) at http://localhost:8080, API at http://localhost:8000
docker compose --project-directory . \
  -f backend/docker-compose.yml \
  -f frontend/docker-compose.yml \
  up --build --attach worker --attach api --attach frontend
