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
