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
#   --list-knowledge --type skill|rule|template|example
#   --seed-knowledge
#   --reset-knowledge
#   --db-console
#   --migrate-schema --all [--dry-run] [--allow-destructive]
#   --migrate-schema --table <table> [--dry-run] [--allow-destructive]
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

COMPOSE="docker compose --project-directory . -f backend/docker-compose.yml -f docker-compose.vps.yml"
API="http://localhost:8000/api/v1"

pretty() {
  python3 -m json.tool 2>/dev/null || cat
}

api() {
  [[ -z "${X_API_KEY:-}" ]] && { echo "ERROR: X_API_KEY is not set. Add it to backend/.env." >&2; exit 1; }
  local method="$1" path="$2" data="${3:-}"
  local args=(-fsS -X "$method" "http://localhost:8000${path}" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${X_API_KEY}")
  [[ -n "$data" ]] && args+=(-d "$data")
  $COMPOSE exec -T api curl "${args[@]}" | pretty
}

require() {
  [[ -n "${2:-}" ]] || { echo "ERROR: $1 requires a value." >&2; exit 1; }
}

CMD="" TYPE="" STATUS="" PAGE="" ARTIFACT_ID="" RAW_PATH="" RAW_DATA="" TABLE_NAME=""
MIGRATE_ALL="" DRY_RUN="" ALLOW_DESTRUCTIVE=""

[[ $# -eq 0 ]] && { grep '^#' "$0" | sed 's/^# \?//'; exit 0; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --health)           CMD=health ;;
    --usage)            CMD=usage ;;
    --db-console)       CMD=db_console ;;
    --migrate-schema)   CMD=migrate_schema ;;
    --seed-knowledge)   CMD=seed_knowledge ;;
    --reset-knowledge)  CMD=reset_knowledge ;;
    --list-artifacts)   CMD=list_artifacts ;;
    --list-jobs)        CMD=list_jobs ;;
    --list-knowledge)   CMD=list_knowledge ;;
    --rm-artifact)      CMD=rm_artifact;   require "$1" "${2:-}"; ARTIFACT_ID="$2"; shift ;;
    --get)              CMD=raw_get;       require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --post)             CMD=raw_post;      require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --patch)            CMD=raw_patch;     require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --delete)           CMD=raw_delete;    require "$1" "${2:-}"; RAW_PATH="$2";    shift ;;
    --table)   require "$1" "${2:-}"; TABLE_NAME="$2"; shift ;;
    --all)     MIGRATE_ALL=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --allow-destructive) ALLOW_DESTRUCTIVE=1 ;;
    --type)    require "$1" "${2:-}"; TYPE="$2";    shift ;;
    --status)  require "$1" "${2:-}"; STATUS="$2";  shift ;;
    --page)    require "$1" "${2:-}"; PAGE="$2";    shift ;;
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
    api DELETE "/internal/artifacts/$ARTIFACT_ID" ;;

  list_jobs)
    path="/api/v1/jobs?"
    [[ -n "$STATUS" ]] && path+="status=$STATUS&"
    [[ -n "$PAGE"   ]] && path+="page=$PAGE&"
    api GET "${path%[?&]}" ;;

  list_knowledge)
    [[ -z "$TYPE" ]] && { echo "ERROR: --list-knowledge requires --type skill|rule|template|example" >&2; exit 1; }
    api GET "/api/v1/knowledge?doc_type=$TYPE" ;;

  seed_knowledge)
    api POST /internal/knowledge/seed ;;

  reset_knowledge)
    $COMPOSE exec -T postgres psql \
      -U "${POSTGRES_USER:-mathanimate}" \
      -d "${POSTGRES_DB:-mathanimate}" \
      -c "DROP TABLE IF EXISTS knowledge_documents;"
    $COMPOSE restart api
    for _ in {1..30}; do
      if api GET /health >/dev/null; then
        $COMPOSE restart worker
        exit 0
      fi
      sleep 2
    done
    echo "ERROR: API health did not recover after resetting knowledge_documents." >&2
    exit 1 ;;

  db_console)
    $COMPOSE exec postgres psql \
      -U "${POSTGRES_USER:-mathanimate}" \
      -d "${POSTGRES_DB:-mathanimate}" ;;

  migrate_schema)
    args=()
    if [[ -n "$MIGRATE_ALL" ]]; then
      args+=(--all)
    else
      [[ -n "$TABLE_NAME" ]] || { echo "ERROR: --migrate-schema requires --all or --table <table>." >&2; exit 1; }
      args+=(--table "$TABLE_NAME")
    fi
    [[ -n "$DRY_RUN" ]] && args+=(--dry-run)
    [[ -n "$ALLOW_DESTRUCTIVE" ]] && args+=(--allow-destructive)
    $COMPOSE exec -T api uv run python -m app.scripts.migrate_schema "${args[@]}" ;;

  raw_get)    api GET    "$RAW_PATH" ;;
  raw_post)   api POST   "$RAW_PATH" "$RAW_DATA" ;;
  raw_patch)  api PATCH  "$RAW_PATH" "$RAW_DATA" ;;
  raw_delete) api DELETE "$RAW_PATH" ;;

  *) echo "No command given. Run without arguments for usage." >&2; exit 1 ;;
esac
