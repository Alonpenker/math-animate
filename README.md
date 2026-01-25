# ManimGenerator

Backend system that generates short instructional math videos using LLM-planned scenes and isolated Manim rendering.

## Structure
- `app/` FastAPI app, configs, and API-facing utilities
- `domain/` Job state machine and domain rules (no IO)
- `services/` Planner/codegen/storage/queue abstractions
- `worker/` Job step orchestration (Celery entrypoints to be added)
- `render/` Docker render invocation (isolated per job)
- `templates/` Parameterized Manim templates
- `shared/` Cross-service constants/helpers
- `tests/` Unit and integration tests

## TODOs (needs decisions)
- Plan/code schemas
  - Option A: Define Pydantic models under `domain/` and reuse across API/worker.
  - Option B: Define Pydantic request/response models under `app/schemas/` and map to domain objects.
- Artifact layout
  - Option A: `job_id/artifacts/{type}/{version}/...`
  - Option B: `job_id/{type}/{version}/...`
- Queue payloads
  - Option A: Minimal `job_id + step` payload.
  - Option B: `job_id + artifact_ids + attempt metadata` payload.
- Render invocation
  - Option A: Shell out to Docker CLI with fixed image tag.
  - Option B: Use docker-py for resource limits + lifecycle tracking.
