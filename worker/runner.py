from __future__ import annotations

from domain.job_state import JobStatus, require_transition


class WorkerRunner:
    """Coordinates job steps; actual implementations live in services/ and render/."""

    def advance(self, job_id: str, current_status: JobStatus, target: JobStatus) -> None:
        require_transition(current_status, target)
        # TODO: Implement step execution + persistence updates.
        # Option A: Single orchestrator per job in worker.
        # Option B: Separate Celery tasks per step with shared state service.
        _ = job_id
        _ = target
