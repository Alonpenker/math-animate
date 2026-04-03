#!/usr/bin/env bash
# admin.sh — call any MathAnimate API route from the VPS host.
# All requests go through `docker compose exec api curl` — port 8000 is never exposed publicly.
#
# Convenience flags:
#   --health
#   --usage
#   --list-jobs [--status <status>] [--page <n>]
#   --list-artifacts [--type video|code|log|plan]
#   --rm-artifact <artifact_id>
#   --list-knowledge --type example|context
#   --create-knowledge --type example|context --title "..." --content "..."
#   --rm-knowledge <document_id>
#   --seed-knowledge
#
# Raw passthrough:
#   --get    <path>
#   --post   <path> [--data '<json>']
#   --patch  <path> [--data '<json>']
#   --delete <path>

set -euo pipefail
cd "$(dirname "$0")/.."

# Load env to pick up X_API_KEY
if [[ -f backend/.env ]]; then
  set -a
  source <(sed 's/\r//' backend/.env)
  set +a
fi
[[ -z "${X_API_KEY:-}" ]] && { echo "ERROR: X_API_KEY is not set. Add it to backend/.env." >&2; exit 1; }

COMPOSE="docker compose --project-directory . -f backend/docker-compose.yml -f docker-compose.vps.yml"
API="http://localhost:8000/api/v1"

pretty() {
  python3 -m json.tool 2>/dev/null || cat
}

api() {
  local method="$1" path="$2" data="${3:-}"
  local args=(-s -X "$method" "http://localhost:8000${path}" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${X_API_KEY}")
  [[ -n "$data" ]] && args+=(-d "$data")
  $COMPOSE exec -T api curl "${args[@]}" | pretty
}

require() {
  [[ -n "${2:-}" ]] || { echo "ERROR: $1 requires a value." >&2; exit 1; }
}

CMD="" TYPE="" STATUS="" PAGE="" ARTIFACT_ID="" DOC_ID="" TITLE="" CONTENT="" RAW_PATH="" RAW_DATA=""

[[ $# -eq 0 ]] && { grep '^#' "$0" | sed 's/^# \?//'; exit 0; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --health)           CMD=health ;;
    --usage)            CMD=usage ;;
    --seed-knowledge)   CMD=seed_knowledge ;;
    --list-artifacts)   CMD=list_artifacts ;;
    --list-jobs)        CMD=list_jobs ;;
    --list-knowledge)   CMD=list_knowledge ;;
    --create-knowledge) CMD=create_knowledge ;;
    --rm-artifact)      CMD=rm_artifact;   require "$1" "${2:-}"; ARTIFACT_ID="$2"; shift ;;
    --rm-knowledge)     CMD=rm_knowledge;  require "$1" "${2:-}"; DOC_ID="$2";      shift ;;
    --get)              CMD=raw_get;       require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --post)             CMD=raw_post;      require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --patch)            CMD=raw_patch;     require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --delete)           CMD=raw_delete;    require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --type)    require "$1" "${2:-}"; TYPE="$2";    shift ;;
    --status)  require "$1" "${2:-}"; STATUS="$2";  shift ;;
    --page)    require "$1" "${2:-}"; PAGE="$2";    shift ;;
    --title)   require "$1" "${2:-}"; TITLE="$2";   shift ;;
    --content) require "$1" "${2:-}"; CONTENT="$2"; shift ;;
    --data)    require "$1" "${2:-}"; RAW_DATA="$2"; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
  shift
done

case "$CMD" in

  health)
    api GET /health ;;

  usage)
    api GET /api/v1/usage ;;

  list_artifacts)
    path="/api/v1/artifacts"
    [[ -n "$TYPE" ]] && path+="?artifact_type=$TYPE"
    api GET "$path" ;;

  rm_artifact)
    $COMPOSE exec -T api curl -s -X DELETE "$API/artifacts/$ARTIFACT_ID" \
      -H "X-API-Key: ${X_API_KEY}" | pretty ;;

  list_jobs)
    path="/api/v1/jobs?"
    [[ -n "$STATUS" ]] && path+="status=$STATUS&"
    [[ -n "$PAGE"   ]] && path+="page=$PAGE&"
    api GET "${path%[?&]}" ;;

  list_knowledge)
    [[ -z "$TYPE" ]] && { echo "ERROR: --list-knowledge requires --type example|context" >&2; exit 1; }
    api GET "/api/v1/knowledge?doc_type=$TYPE" ;;

  rm_knowledge)
    $COMPOSE exec -T api curl -s -X DELETE "$API/knowledge/$DOC_ID" \
      -H "X-API-Key: ${X_API_KEY}" | pretty ;;

  create_knowledge)
    [[ -z "$TYPE" || -z "$TITLE" || -z "$CONTENT" ]] && {
      echo "ERROR: --create-knowledge requires --type, --title, and --content" >&2; exit 1; }
    payload=$(python3 -c "
import json, sys
print(json.dumps({'doc_type': sys.argv[1], 'title': sys.argv[2], 'content': sys.argv[3]}))" \
      "$TYPE" "$TITLE" "$CONTENT")
    api POST /api/v1/knowledge "$payload" ;;

  seed_knowledge)
    api POST /api/v1/knowledge/seed ;;

  raw_get)    api GET    "$RAW_PATH" ;;
  raw_post)   api POST   "$RAW_PATH" "$RAW_DATA" ;;
  raw_patch)  api PATCH  "$RAW_PATH" "$RAW_DATA" ;;
  raw_delete) api DELETE "$RAW_PATH" ;;

  *) echo "No command given. Run without arguments for usage." >&2; exit 1 ;;
esac
