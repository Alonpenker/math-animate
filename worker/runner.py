from __future__ import annotations

from domain.job_state import JobStatus, require_transition


class WorkerRunner:
    """Coordinates job steps; actual implementations live in services/ and render/."""

    def advance(self, job_id: str, current_status: JobStatus) -> None:
        if current_status == JobStatus.CREATED:
            self.handle_planning(job_id,current_status)
        if current_status == JobStatus.PLANNED:
            self.handle_codegen(job_id,current_status)
        if current_status == JobStatus.CODED:
            self.handle_render(job_id,current_status)
        else:
            raise NotImplementedError

    def handle_planning(self, job_id: str, current_status: JobStatus) -> dict:
        if current_status != JobStatus.CREATED:
            return self._invalid_state(job_id, current_status, JobStatus.CREATED)
        # TODO: Implement planning step orchestration.
        pass
        return {"status": "ok"}

    def handle_codegen(self, job_id: str, current_status: JobStatus) -> dict:
        if current_status != JobStatus.APPROVED:
            return self._invalid_state(job_id, current_status, JobStatus.APPROVED)
        # TODO: Implement codegen step orchestration.
        pass
        return {"status": "ok"}

    def handle_render(self, job_id: str, current_status: JobStatus) -> dict:
        if current_status != JobStatus.CODED:
            return self._invalid_state(job_id, current_status, JobStatus.CODED)
        # TODO: Implement render step orchestration.
        pass
        return {"status": "ok"}

    def _invalid_state(
        self, job_id: str, current_status: JobStatus, expected: JobStatus
    ) -> dict:
        return {
            "status": "invalid_state",
            "job_id": job_id,
            "current_status": current_status.value,
            "expected_status": expected.value,
        }
