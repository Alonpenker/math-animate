from typing import Optional
from uuid import UUID

import redis

from app.schemas.jobs import Job
from app.domain.job_state import JobStatus, is_terminal
from app.dependencies.redis_client import TERMINAL_JOB_TTL_SECONDS


class JobsRepository:

    KEY_PREFIX = "job"

    @staticmethod
    def _key(job_id: UUID) -> str:
        return f"{JobsRepository.KEY_PREFIX}:{job_id}"

    @classmethod
    def create_job(cls, r: redis.Redis, job: Job) -> None:
        r.set(cls._key(job.job_id), job.status.value)

    @classmethod
    def get_job(cls, r: redis.Redis, job_id: UUID) -> Optional[Job]:
        value = r.get(cls._key(job_id))
        if value is None:
            return None
        return Job(job_id=job_id, status=JobStatus(value.decode()))

    @classmethod
    def update_job_status(cls, r: redis.Redis, job_id: UUID, status: JobStatus) -> None:
        if is_terminal(status):
            r.set(cls._key(job_id), status.value, ex=TERMINAL_JOB_TTL_SECONDS)
        else:
            r.set(cls._key(job_id), status.value)
