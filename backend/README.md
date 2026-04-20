# MathAnimate

> **AI-powered backend that turns a teacher's lesson idea into a rendered math animation — automatically.**

Teachers submit a lesson topic → an LLM drafts a structured scene plan → the teacher reviews and approves → Manim code is generated, verified, and rendered in an isolated container → video artifacts are stored and ready to download.

---

## Features

- **Human-in-the-loop approval** — the teacher reviews the scene plan before any code is generated
- **RAG-augmented generation** — planning and codegen prompts are enriched with similar, high-quality examples via vector similarity search
- **Auto-fix pipeline** — generated code that fails verification is automatically patched by the LLM and re-verified before failing permanently
- **Sandboxed rendering** — every render runs in a fresh, network-isolated Docker container with strict CPU, memory, and PID limits
- **Token budget enforcement** — a 250K daily token cap with pessimistic reservation and per-job ledger tracking prevents runaway LLM spend
- **OpenAI-backed LLM pipeline** — planning and code generation run on OpenAI chat models configured in one place
- **OpenAPI docs** — full Swagger UI available at `/docs` out of the box

---

## Architecture

Three distinct runtime images share no code at render time:

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT                               │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP
                        ▼
┌───────────────────────────────────────────────────────────┐
│  API  (FastAPI · port 8000)                               │
│  Enqueues work only — no blocking execution               │
│  Routes: /jobs  /artifacts  /knowledge  /usage            │
└──────────┬─────────────────────────────────────┬──────────┘
           │ RabbitMQ (tasks)                    │ Redis (state)
           ▼                                     │
┌──────────────────────────────┐                 │
│  WORKER  (Celery)            │◄────────────────┘
│  generate_plan               │
│  generate_code               │
│  verify_code_task            │
│  fix_code_task               │
│  generate_render ────────────┼──► docker run manimcommunity/manim
└──────────────────────────────┘         (no network · isolated /job)
           │                   │
           ▼                   ▼
      PostgreSQL             MinIO
    (pgvector · state)   (artifact storage)
```

### Runtime Images

| Image | Entry point | Responsibilities |
|---|---|---|
| **api** | `uvicorn app.main:app` | HTTP, request validation, job creation, artifact access |
| **worker** | `celery -A app.workers.worker worker` | LLM calls, verification, render orchestration, Docker socket access |
| **renderer** | `manimcommunity/manim:v0.19.2` | Manim execution only — no app code, no network |

---

## Job Lifecycle

Every job moves through a strictly enforced state machine. Illegal transitions raise an error immediately.

```
                          ┌──────────┐
                          │ CREATED  │
                          └────┬─────┘
                               │ generate_plan
                          ┌────▼─────┐
                          │ PLANNING │
                          └────┬─────┘
                    ┌──────────┤
              FAILED │          │ OK
                    ▼          ▼
            FAILED_PLANNING  PLANNED
                               │ teacher approves
                          ┌────▼─────┐
                          │ APPROVED │
                          └────┬─────┘
                               │ generate_code
                          ┌────▼─────┐
                          │ CODEGEN  │
                          └────┬─────┘
                    ┌──────────┤
              FAILED │          │ OK
                    ▼          ▼
            FAILED_CODEGEN   CODED
                               │ verify_code_task
                          ┌────▼──────┐
                          │ VERIFYING │
                          └────┬──────┘
               ┌───────────────┼───────────────┐
             OK│         NEEDS FIX│        FAILED│
               ▼               ▼               ▼
           VERIFIED         FIXING     FAILED_VERIFICATION
               │         fix_code_task
               │           (1 retry)
               │               │
               └───────────────┘ (re-verify)
               │
          ┌────▼──────┐
          │ RENDERING │
          └────┬──────┘
     ┌─────────┤
FAILED│         │ OK
     ▼          ▼
FAILED_RENDER  RENDERED

All non-terminal states + RENDERED ──► CANCELLED
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| Task queue | Celery + RabbitMQ |
| Job state | Redis |
| Database | PostgreSQL 16 + pgvector |
| Artifact storage | MinIO (S3-compatible) |
| Embeddings | Ollama (`nomic-embed-text`, 768 dims) |
| LLM | LangChain (OpenAI) |
| Renderer | `manimcommunity/manim:v0.19.2` (Docker-in-Docker) |
| Package manager | `uv` |
| Language | Python 3.13 |

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) with Compose v2
- An **OpenAI** API key

### 1. Configure environment

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `API_KEY` | OpenAI API key |
| `STORAGE_ACCESS_KEY` | MinIO root user |
| `STORAGE_SECRET_KEY` | MinIO root password |
| `STORAGE_BUCKET` | Bucket name for artifacts |
| `STORAGE_ENDPOINT` | MinIO endpoint (e.g. `http://minio:9000`) |
| `DATABASE_URL` | PostgreSQL connection string |
| `BROKER_URL` | RabbitMQ AMQP URL |
| `REDIS_URL` | Redis connection URL |
| `OLLAMA_BASE_URL` | Ollama API base URL |

### 2. Start the stack

**Backend only** (API + worker + all supporting services):

```bash
docker-compose up
```

**Full stack** (adds the frontend served by NGINX at port 80):

```bash
docker-compose -f docker-compose.yml -f docker-compose.frontend.yml up
```

This pulls and starts all services, including downloading the Manim image and the `nomic-embed-text` embedding model. First boot takes a few minutes.

The API is available at **http://localhost:8000** — interactive docs at **http://localhost:8000/docs**.
The frontend (full stack only) is available at **http://localhost:80**.

### 3. Seed the knowledge base

Pre-prepared plan and code examples are bundled in `app/examples/`. Seed them once after first boot:

```bash
scripts/admin.sh --seed-knowledge
```

### E2E mode (no LLM calls)

Start the stack with stubbed LLM responses for integration testing without spending tokens:

```bash
# bash
E2E=true docker-compose up

# PowerShell
$env:E2E="true"; docker-compose up
Remove-Item Env:E2E
```

---

## API Reference

All routes are prefixed with `/api/v1`. Full interactive docs at `/docs`.

### Jobs

| Method | Path | Description |
|---|---|---|
| `POST` | `/jobs` | Create a new generation job |
| `GET` | `/jobs/{job_id}/status` | Poll job state |
| `GET` | `/jobs/{job_id}/plan` | Retrieve the generated scene plan |
| `PATCH` | `/jobs/{job_id}/approve?approved=true` | Approve or reject the plan |

**Create job request body:**

```json
{
  "topic": "Solving two-step equations",
  "misconceptions": ["students forget to apply inverse operations to both sides"],
  "constraints": ["no more than 3 steps per scene", "label every operation"],
  "examples": ["4x + 2 = 10"],
  "number_of_scenes": 2
}
```

### Artifacts

| Method | Path | Description |
|---|---|---|
| `GET` | `/artifacts` | List artifacts (filter by `job_id`, `artifact_type`) |
| `GET` | `/artifacts/{artifact_id}` | Get artifact metadata |
| `GET` | `/artifacts/{artifact_id}/download` | Stream artifact file |
| `DELETE` | `/artifacts/{artifact_id}` | Delete artifact |

Artifact types: `mp4` (rendered video), `py` (generated Manim code), `log` (render logs), `plan` (scene plan JSON).

### Knowledge Base

| Method | Path | Description |
|---|---|---|
| `POST` | `/knowledge` | Add a document (plan or code example) |
| `POST` | `/knowledge/seed` | Seed bundled examples |
| `GET` | `/knowledge?doc_type=plan\|code` | List documents by type |
| `GET` | `/knowledge/{document_id}` | Get a document |
| `DELETE` | `/knowledge/{document_id}` | Delete a document |

### Usage

| Method | Path | Description |
|---|---|---|
| `GET` | `/usage` | Daily token consumption summary |

---

## Project Structure

```
app/
├── configs/          # App and LLM settings (model, prompts, budget thresholds)
├── dependencies/     # FastAPI DI providers (DB pool, Redis, storage)
├── domain/           # Pure business logic — job_state.py (zero I/O)
├── examples/         # Pre-prepared plan/code examples for RAG seeding
├── exceptions/       # Custom exception types and global handler
├── repositories/     # SQL query execution (jobs, plans, artifacts, knowledge, token ledger)
├── routes/           # FastAPI routers: jobs, artifacts, knowledge, usage
├── schemas/          # Pydantic v2 DTOs for all I/O boundaries
├── services/         # External system abstractions
│   ├── llm_service.py          # LangChain wrapper, prompt rendering, RAG injection
│   ├── rag_service.py          # pgvector + Ollama similarity search
│   ├── budget_service.py       # Token reservation and reconciliation
│   └── files_storage_service.py # MinIO artifact upload/download
├── utils/            # Structured logging, E2E stubs
└── workers/
    ├── worker.py           # Celery task definitions (5 tasks)
    ├── worker_helpers.py   # Shared task utilities (transitions, budget, storage)
    ├── worker_settings.py  # Docker commands and path constants
    └── runner.py           # WorkerRunner — enqueues the correct task per job state
tests/                # Unit and integration tests
```

### Dependency rule

`routes` and `workers` → `repositories` + `services`. The reverse is never allowed.

---

## Configuration

### LLM model configuration

Edit [app/configs/llm_settings.py](app/configs/llm_settings.py):

```python
LLM_PROVIDER = "openai"
LLM_PLAN_MODEL = "gpt-5.2"
LLM_CODE_MODEL = "gpt-5.1-codex"
```

Set your key in `.env`:

```
API_KEY=sk-...
```

### Token budget

```python
DAILY_TOKEN_LIMIT            = 250_000   # hard cap
SOFT_THRESHOLD_RATIO         = 0.8       # warning threshold
```

---

## Development

```bash
# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_jobs.py

# Rebuild backend images after a code change, then restart
docker compose build api worker
docker-compose up --attach worker --attach api

# Backend-only stack with E2E stubs (bash)
E2E=true docker-compose up --attach worker --attach api

# Full stack (frontend at http://localhost:80)
docker-compose -f docker-compose.yml -f docker-compose.frontend.yml up --attach worker --attach api --attach frontend

# Rebuild frontend after a frontend code change
docker compose -f docker-compose.yml -f docker-compose.frontend.yml build frontend

# Frontend-only dev server (Vite HMR, no Docker — requires backend already running)
cd ../frontend && npm run dev
```

---

## Infrastructure Services

`docker-compose.yml` — backend stack:

| Service | Image | Purpose | Port |
|---|---|---|---|
| `api` | project image | FastAPI HTTP server | 8000 |
| `worker` | project image | Celery task runner | — |
| `docker-daemon` | `docker:dind` | Isolated Manim rendering | — |
| `postgres` | `pgvector/pgvector:pg16` | Job state + knowledge vectors | 5432 |
| `redis` | `redis:7-alpine` | Celery backend + job cache | 6379 |
| `rabbitmq` | `rabbitmq:4-alpine` | Celery broker | 5672 |
| `minio` | `minio/minio` | Artifact object storage | 9000 / 9001 |
| `ollama` | `ollama/ollama` | Local embedding model | 11434 |

`docker-compose.frontend.yml` — add-on for full-stack local testing:

| Service | Image | Purpose | Port |
|---|---|---|---|
| `frontend` | project image | NGINX serving React build, proxies `/api/` to the backend | 80 |

---

## Security & Safety

- **Manim code never executes in the API or worker process** — only inside a locked-down renderer container
- Renderer container has: no network access, CPU quota, memory limit, PID cap, and only `/job` mounted
- Schema validation is enforced on every I/O boundary via Pydantic v2 — never skipped
- Stale token reservations are reconciled automatically every 15 minutes

---

## License

[MIT](LICENSE)
