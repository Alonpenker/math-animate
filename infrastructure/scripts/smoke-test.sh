#!/usr/bin/env bash
# smoke-test.sh — End-to-end smoke test for the MathAnimate production stack
#
# Validates the full happy path:
#   1. Health check
#   2. Create a job
#   3. Poll until PLANNED status
#   4. Approve the plan
#   5. Poll until RENDERED (or failure state) with timeout
#
# Usage: ./smoke-test.sh <api-base-url> <api-key>
#
# Example:
#   ./smoke-test.sh http://my-alb-123.eu-north-1.elb.amazonaws.com sk-myapikey
#
# Exit codes:
#   0 — all steps passed
#   1 — any step failed

set -euo pipefail

# ── Argument validation ────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <api-base-url> [api-key]" >&2
  exit 1
fi

API_BASE_URL="${1%/}"
API_KEY="${2:-}"  # Optional — the API does not currently enforce endpoint auth

# ── Configuration ──────────────────────────────────────────────────────────────
PLAN_TIMEOUT=300      # seconds to wait for PLANNED state
RENDER_TIMEOUT=600    # seconds to wait for RENDERED state
POLL_INTERVAL=10      # seconds between status polls

FAILED=0

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; FAILED=1; }
info() { echo -e "${YELLOW}[INFO]${NC} $*"; }

# ── HTTP helper ────────────────────────────────────────────────────────────────
api_call() {
  local method="$1"
  local path="$2"
  local data="${3:-}"

  local curl_args=(
    --silent
    --max-time 30
    --write-out "\n%{http_code}"
    -X "${method}"
    -H "Content-Type: application/json"
  )

  # Include API key header only if one was provided
  if [[ -n "${API_KEY}" ]]; then
    curl_args+=(-H "X-API-Key: ${API_KEY}")
  fi

  if [[ -n "${data}" ]]; then
    curl_args+=(-d "${data}")
  fi

  curl "${curl_args[@]}" "${API_BASE_URL}${path}"
}

# Splits response into body and HTTP status code
parse_response() {
  local raw="$1"
  echo "${raw}" | head -n -1  # body
}

parse_status() {
  local raw="$1"
  echo "${raw}" | tail -n1    # status code
}

# ── Step 1: Health check ───────────────────────────────────────────────────────
echo ""
info "Step 1: Health check"

HEALTH_RESPONSE=$(curl --silent --max-time 15 --write-out "\n%{http_code}" \
  "${API_BASE_URL}/health" || echo -e "\n000")
HEALTH_STATUS=$(parse_status "${HEALTH_RESPONSE}")
HEALTH_BODY=$(parse_response "${HEALTH_RESPONSE}")

if [[ "${HEALTH_STATUS}" == "200" ]]; then
  pass "Health check passed (HTTP ${HEALTH_STATUS})"
else
  fail "Health check failed (HTTP ${HEALTH_STATUS}): ${HEALTH_BODY}"
  echo ""
  echo "Aborting smoke test — API is not reachable." >&2
  exit 1
fi

# ── Step 2: Create a job ───────────────────────────────────────────────────────
echo ""
info "Step 2: Create a job"

JOB_PAYLOAD='{
  "topic": "smoke-test: solving one-step equations",
  "misconceptions": ["students forget to apply the same operation to both sides"],
  "constraints": ["use simple whole numbers only", "include a balance scale analogy"],
  "examples": [],
  "number_of_scenes": 1
}'

JOB_RESPONSE=$(api_call POST "/api/v1/jobs" "${JOB_PAYLOAD}" || echo -e "\n000")
JOB_STATUS=$(parse_status "${JOB_RESPONSE}")
JOB_BODY=$(parse_response "${JOB_RESPONSE}")

if [[ "${JOB_STATUS}" != "201" ]]; then
  fail "Job creation failed (HTTP ${JOB_STATUS}): ${JOB_BODY}"
  exit 1
fi

JOB_ID=$(echo "${JOB_BODY}" | python3 -c "import sys,json; print(json.load(sys.stdin)['job']['job_id'])" 2>/dev/null || echo "")

if [[ -z "${JOB_ID}" ]]; then
  fail "Could not extract job_id from response: ${JOB_BODY}"
  exit 1
fi

pass "Job created (HTTP ${JOB_STATUS}) — job_id=${JOB_ID}"

# ── Step 3: Poll until PLANNED ─────────────────────────────────────────────────
echo ""
info "Step 3: Polling for PLANNED status (timeout: ${PLAN_TIMEOUT}s)..."

ELAPSED=0
CURRENT_STATUS=""

while [[ ${ELAPSED} -lt ${PLAN_TIMEOUT} ]]; do
  STATUS_RESPONSE=$(api_call GET "/api/v1/jobs/${JOB_ID}/status" || echo -e "\n000")
  STATUS_HTTP=$(parse_status "${STATUS_RESPONSE}")
  STATUS_BODY=$(parse_response "${STATUS_RESPONSE}")

  CURRENT_STATUS=$(echo "${STATUS_BODY}" | python3 -c "import sys,json; print(json.load(sys.stdin)['job']['status'])" 2>/dev/null || echo "UNKNOWN")

  info "  Status: ${CURRENT_STATUS} (${ELAPSED}s elapsed)"

  case "${CURRENT_STATUS}" in
    PLANNED)
      pass "Job reached PLANNED state after ${ELAPSED}s"
      break
      ;;
    FAILED_PLANNING)
      fail "Job failed during planning: ${STATUS_BODY}"
      exit 1
      ;;
    CANCELLED)
      fail "Job was cancelled unexpectedly"
      exit 1
      ;;
  esac

  sleep "${POLL_INTERVAL}"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

if [[ "${CURRENT_STATUS}" != "PLANNED" ]]; then
  fail "Job did not reach PLANNED within ${PLAN_TIMEOUT}s. Last status: ${CURRENT_STATUS}"
  exit 1
fi

# ── Step 4: Approve the plan ───────────────────────────────────────────────────
echo ""
info "Step 4: Approving the plan"

APPROVE_RESPONSE=$(api_call PATCH "/api/v1/jobs/${JOB_ID}/approve?approved=true" || echo -e "\n000")
APPROVE_STATUS=$(parse_status "${APPROVE_RESPONSE}")
APPROVE_BODY=$(parse_response "${APPROVE_RESPONSE}")

if [[ "${APPROVE_STATUS}" != "200" ]]; then
  fail "Plan approval failed (HTTP ${APPROVE_STATUS}): ${APPROVE_BODY}"
  exit 1
fi

pass "Plan approved (HTTP ${APPROVE_STATUS})"

# ── Step 5: Poll until RENDERED (or failure state) ────────────────────────────
echo ""
info "Step 5: Polling for RENDERED status (timeout: ${RENDER_TIMEOUT}s)..."

ELAPSED=0
CURRENT_STATUS=""
TERMINAL_STATES=("RENDERED" "FAILED_CODEGEN" "FAILED_RENDER" "CANCELLED")

while [[ ${ELAPSED} -lt ${RENDER_TIMEOUT} ]]; do
  STATUS_RESPONSE=$(api_call GET "/api/v1/jobs/${JOB_ID}/status" || echo -e "\n000")
  STATUS_BODY=$(parse_response "${STATUS_RESPONSE}")

  CURRENT_STATUS=$(echo "${STATUS_BODY}" | python3 -c "import sys,json; print(json.load(sys.stdin)['job']['status'])" 2>/dev/null || echo "UNKNOWN")

  info "  Status: ${CURRENT_STATUS} (${ELAPSED}s elapsed)"

  # Check if we've reached a terminal state
  for terminal in "${TERMINAL_STATES[@]}"; do
    if [[ "${CURRENT_STATUS}" == "${terminal}" ]]; then
      break 2  # Break out of both the for loop and while loop
    fi
  done

  sleep "${POLL_INTERVAL}"
  ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

# Evaluate final status
case "${CURRENT_STATUS}" in
  RENDERED)
    pass "Job completed successfully — status=RENDERED after ${ELAPSED}s"
    ;;
  FAILED_CODEGEN)
    fail "Job failed during code generation (status=${CURRENT_STATUS})"
    FAILED=1
    ;;
  FAILED_RENDER)
    fail "Job failed during rendering (status=${CURRENT_STATUS})"
    FAILED=1
    ;;
  CANCELLED)
    fail "Job was cancelled unexpectedly (status=${CURRENT_STATUS})"
    FAILED=1
    ;;
  *)
    fail "Job did not reach RENDERED within ${RENDER_TIMEOUT}s. Last status: ${CURRENT_STATUS}"
    FAILED=1
    ;;
esac

# ── Summary ────────────────────────────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
if [[ ${FAILED} -eq 0 ]]; then
  pass "Smoke test PASSED — all steps completed successfully"
  echo "──────────────────────────────────────────────"
  exit 0
else
  fail "Smoke test FAILED — see above for details"
  echo "──────────────────────────────────────────────"
  echo ""
  echo "For detailed logs, check CloudWatch:"
  echo "  /mathanimate/ecs/api    — API container logs"
  echo "  /mathanimate/ec2/worker — Worker instance logs"
  exit 1
fi
