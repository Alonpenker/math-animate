# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Backend system that generates short instructional 8th-grade math videos using LLM-planned scenes and isolated Manim rendering. Teachers submit a lesson request → LLM generates a scene plan → teacher approves → Manim code is generated and rendered into video.

## Commands

All commands use `uv` as the package manager (never `pip` or `python` directly).

```bash
# Run the API server locally
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run the Celery worker locally
uv run celery -A app.workers.worker worker

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_jobs.py

# Run type checking
uv run mypy .

# Start the full stack (preferred for development)
docker-compose up
```

## Architecture

### Service Boundaries

Single repository, three distinct runtime images:
- **API** (`app/main.py`): FastAPI routes for job control, artifact access, knowledge management, and usage reporting. Routes **enqueue work only** — no blocking execution.
- **Worker** (`app/workers/worker.py`): Celery consumer that runs planning, code generation, and render orchestration. Has access to Docker socket for spawning renderer containers.
- **Renderer**: Isolated Docker container with Manim runtime. **No app code dependency, no network access.** Only `/job` directory is mounted.

### Job State Machine (NON-NEGOTIABLE)

Defined in [app/domain/job_state.py](app/domain/job_state.py). Never bypass `require_transition()`.

```
CREATED → PLANNING → PLANNED → APPROVED → CODEGEN → CODED → RENDERING → RENDERED
                  ↓                     ↓         ↓
           FAILED_PLANNING      FAILED_CODEGEN  FAILED_RENDER
```

All terminal states plus `RENDERED` can transition to `CANCELLED`.

### Worker Pipeline

Three Celery tasks in sequence (each enqueues the next on success):
1. **`generate_plan`** — reserves token budget, calls LLM with RAG examples, stores plan artifact
2. **`generate_code`** — reserves token budget, calls LLM, runs syntax/import verification, retries once on failure
3. **`generate_render`** — spawns isolated Docker container, collects video + logs as artifacts

### Package Layout

```
app/
├── configs/        # Settings (app_settings.py, llm_settings.py)
├── dependencies/   # FastAPI DI (db pool, storage, services)
├── domain/         # Pure business logic — job_state.py (no I/O)
├── examples/       # Pre-prepared plan/code examples for RAG seeding
├── repositories/   # SQL query execution (jobs, plans, artifacts, knowledge, token_ledger)
├── routes/         # FastAPI routers: jobs, artifacts, knowledge, usage
├── schemas/        # Pydantic v2 DTOs for all I/O
├── services/       # External system abstractions (LLM, storage, RAG, budget)
├── utils/          # Loggers and shared helpers
└── workers/        # Celery task definitions
```

**Dependency rule:** `routes` and `workers` → `repositories` + `services`. Never the reverse.

### Key Services

- **`LLMService`** (`app/services/llm_service.py`): Wraps LangChain (OpenAI/Anthropic), fetches RAG examples before each LLM call, handles planning and codegen prompts.
- **`RAGService`**: Vector similarity search via pgvector + Ollama `nomic-embed-text` embeddings (768 dimensions).
- **`BudgetService`**: Enforces a 250K daily token limit (soft threshold at 80%). Reserves tokens before LLM calls and settles after.
- **`FilesStorageService`**: MinIO artifact storage. All artifact access uses artifact IDs, never raw paths.

### LLM Configuration

Centralized in [app/configs/llm_settings.py](app/configs/llm_settings.py). Change model, temperature, token limits, and system prompts there. The system prompts use `{examples}` placeholder injected by `LLMService` at call time.

### Data Model

- All external I/O uses Pydantic schemas in `app/schemas/`.
- Plans and generated code are stored as JSON/text artifacts, not implicit state.
- Artifacts are typed: `video`, `code`, `log`, `plan`.
- Token usage is tracked per-job in `token_ledger` table.

## Infrastructure (docker-compose)

| Service | Purpose | Port |
|---|---|---|
| api | FastAPI | 8000 |
| worker | Celery | — |
| docker-daemon | Docker-in-Docker for rendering | — |
| postgres | pgvector-enabled DB | 5432 |
| redis | Celery result backend | 6379 |
| rabbitmq | Celery broker | 5672 |
| minio | Artifact storage (S3-compatible) | 9000 |
| ollama | Local embedding model | 11434 |

## Critical Constraints

- **Manim code never executes in the API or worker process** — only in the isolated renderer container.
- **Rendering is always per-job Docker container** with no network, CPU/memory/time limits, only `/job` mounted.
- The renderer image has no dependency on any `app/` code.
- Schema validation is never skipped.
- Stale token reservations are cleaned up after 30 minutes (background task).

## Code Style

- Python 3.13+ — do **not** add `from __future__ import annotations`.
- Keep imports minimal and explicit.
- Follow existing conventions over external "best practices."
- If something is unclear: write a TODO and propose 2 explicit options — do not guess.
