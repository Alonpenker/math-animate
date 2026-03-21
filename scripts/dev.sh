#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

# Backend only, API at http://localhost:8000
docker compose --project-directory . -f backend/docker-compose.yml up --build --attach worker --attach api
