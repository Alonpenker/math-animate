#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "=== Starting frontend dev server in background (http://localhost:5174) ==="
(cd frontend && npm run dev > /dev/null 2>&1) &
FRONTEND_PID=$!
trap "kill $FRONTEND_PID 2>/dev/null" EXIT

echo "=== Starting backend stack (api + worker logs) ==="
docker compose --project-directory . -f backend/docker-compose.yml up --build --attach worker --attach api
