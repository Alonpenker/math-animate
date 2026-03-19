#!/usr/bin/env bash
# seed-knowledge.sh — Seed the RAG knowledge base into the production API
#
# Calls the live API's /api/v1/knowledge/seed endpoint which internally reads the
# bundled examples from the container filesystem and inserts them into the database.
# The endpoint is idempotent — existing documents are skipped.
#
# Usage: ./seed-knowledge.sh <api-base-url> <api-key>
#
# Example:
#   ./seed-knowledge.sh http://my-alb-123.eu-north-1.elb.amazonaws.com sk-myapikey

set -euo pipefail

# ── Argument validation ────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <api-base-url> [api-key]" >&2
  exit 1
fi

API_BASE_URL="${1%/}"  # Strip trailing slash if present
API_KEY="${2:-}"       # Optional — the seed endpoint does not require endpoint auth

SEED_ENDPOINT="${API_BASE_URL}/api/v1/knowledge/seed"

echo "==> Seeding RAG knowledge base"
echo "    Endpoint: ${SEED_ENDPOINT}"
echo ""

# ── Wait for the API to be healthy before seeding ─────────────────────────────
echo "==> Waiting for API to be healthy..."
MAX_HEALTH_WAIT=120
ELAPSED=0
while [[ ${ELAPSED} -lt ${MAX_HEALTH_WAIT} ]]; do
  HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
    --max-time 10 \
    "${API_BASE_URL}/health" 2>/dev/null || echo "000")

  if [[ "${HTTP_STATUS}" == "200" ]]; then
    echo "    API is healthy (HTTP ${HTTP_STATUS})"
    break
  fi

  echo "    Waiting... (HTTP ${HTTP_STATUS}, ${ELAPSED}s elapsed)"
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done

if [[ "${HTTP_STATUS}" != "200" ]]; then
  echo "ERROR: API did not become healthy within ${MAX_HEALTH_WAIT}s" >&2
  exit 1
fi

echo ""

# ── Trigger the seed endpoint ─────────────────────────────────────────────────
echo "==> Calling seed endpoint..."

CURL_ARGS=(
  -sf
  --max-time 120
  -X POST
  -H "Content-Type: application/json"
)
if [[ -n "${API_KEY}" ]]; then
  CURL_ARGS+=(-H "X-API-Key: ${API_KEY}")
fi

RESPONSE=$(curl "${CURL_ARGS[@]}" "${SEED_ENDPOINT}")

if [[ $? -ne 0 ]]; then
  echo "ERROR: Failed to call seed endpoint" >&2
  exit 1
fi

echo "    Response: ${RESPONSE}"

# Extract inserted/skipped counts from JSON response
INSERTED=$(echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('inserted', '?'))" 2>/dev/null || echo "?")
SKIPPED=$(echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('skipped', '?'))" 2>/dev/null || echo "?")

echo ""
echo "==> Seed complete."
echo "    Inserted: ${INSERTED}"
echo "    Skipped:  ${SKIPPED} (already existed — idempotent)"
