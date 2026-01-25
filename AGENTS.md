# AGENTS instructions

## Project Context
* **Domain:** Backend system that generates short instructional math videos (8th-grade linear algebra) using LLM-planned scenes and Manim rendering.
* **Core workflows:**
  * Teacher submits lesson input → system generates a scene plan → teacher approves → system renders video.
  * Asynchronous job execution with isolated rendering.
  * Artifact storage and retrieval (video, logs, plans).
* **Quality priorities:** correctness, simplicity
* **Hard constraints:**
  * Local-first execution
  * Rendering must run in isolated Docker environment
  * Template-first Manim generation (no free-form code in MVP)

## Operating Rules (anti-hallucination, ALWAYS)
* Do not invent endpoints, schemas, job states, or services. Search the repo first.
* Prefer minimal, local changes. No unrelated refactors.
* Respect the job state machine; never bypass required transitions.
* Keep the system runnable locally at all times.
* If something is unclear: write TODO + propose **2 explicit options**. Do not guess.
* Follow existing project conventions over “best practices” if they conflict.

## Code Style
* Do NOT add `from __future__ import annotations` - not needed for Python 3.11+
* Keep imports minimal and explicit

## Stack (EDITABLE)
### Defaults
* Language: Python 3.11+
* Package manager: uv
* Web API: FastAPI
* Validation: Pydantic v2
* Async tasks / queue: Redis + Celery worker
* Database: SQLite (MVP), Postgres later
* Rendering: Manim (pinned version) in Docker
* Storage: Local filesystem (artifact abstraction required)
* LLM integration: OpenAI (planner + codegen), optional RAG
### Forbidden
* Executing Manim or generated code inside API or worker process
* Long-running or blocking work in API routes
* Skipping schema validation
* Writing files outside the job workspace
* Logging secrets, API keys, or full prompts with sensitive data

## Architecture
### Services (single repo, multiple images)
* **API service:** FastAPI routes, job control, artifact access
* **Worker service:** queue consumer, planning, codegen, render orchestration
* **Renderer image:** Manim runtime + minimal entrypoint only (no app logic)
### Package layout (guideline)
* `app/routes/` – FastAPI routers + request/response DTOs
* `app/schemas/` – models + request/response DTOs
* `app/persistence/` – data mapping (ORM).
* `app/configs/` – configuration files + global constants
* `app/services/` – business logic
* `app/utils/` – utility functions, loggers, and shared helpers
* `app/main.py` - FastAPI app entry point + middleware
* `domain/` – schemas, job state machine, enums (no FastAPI, no IO)
* `services/` – planner, codegen, storage, queue abstractions
* `worker/` – job consumers and step execution
* `render/` – render contracts and Docker invocation logic
* `templates/` – Manim scene templates (parameterized)
* `shared/` – constants, utilities used across services
* `tests/` - unit tests + integration test
### Dependency rules
* API → services
* Worker → domain + services
* Domain → no FastAPI, no Redis, no Docker, no filesystem
* Renderer → **no dependency on app code**

## Job & State Model (NON-NEGOTIABLE)
* Canonical states:
  * `CREATED → PLANNING → PLANNED → APPROVED → CODEGEN → CODED → RENDER_QUEUED → RENDERING → RENDERED`
  * Failure states: `FAILED_PLANNING`, `FAILED_CODEGEN`, `FAILED_RENDER`
* Only **approved plans** may proceed to code generation.
* Each plan, code bundle, and render run is **versioned and immutable**.
* Retries must be explicit and recorded.

## API & Error Model (EDITABLE)
### REST conventions
* Base path: `/api/v1`
* Resource naming: nouns (`jobs`, `artifacts`)
* API routes enqueue work; they do not execute it.
* Responses must include job_id and current status.
### Errors
* Use a global exception handler.
* Never return stack traces to the client.
* Map expected failures to typed error responses (validation, state violation, not found).
* Render/runtime errors are exposed via logs, not raw exceptions.
## Data & Artifacts
* All external input/output uses Pydantic schemas.
* Plans and code are stored as JSON/text artifacts, never implicit state.
* Videos, logs, and metadata are stored per-job.
* Artifact access is always via artifact IDs, not raw paths.

## Rendering Rules (CRITICAL)
* Rendering must run in a **separate Docker container per job**.
* Renderer container:
  * No network access
  * CPU/memory/time limits
  * Only `/job` directory mounted
* Worker is responsible for:
  * Preparing inputs
  * Verify code
  * Call LLM
  * Invoking renderer
  * Collecting outputs and logs
* Renderer must be reproducible (pinned Manim + deps).

## Logging & Observability
* Structured logs with: job_id, step, attempt, duration.
* Every failure must store:
  * error category
  * stderr/stdout paths
  * render exit code (if applicable)
* Silence is failure. If something breaks, it must be traceable.

## Testing
* Unit tests for:
  * Job state transitions
  * Plan/code schema validation
  * Template parameter filling
* Integration test:
  * One full happy-path job (mock renderer if needed)
* Rendering itself does **not** need to be tested in CI, but must be reproducible locally.