from typing import Optional
from uuid import UUID

from app.schemas.jobs import Job, JobSchema
from app.domain.job_state import JobStatus
from app.repositories.repository import Repository

class JobsRepository(Repository):

    TABLE_NAME = 'jobs'
    SCHEMA = JobSchema
    PRIMARY_KEY = 'job_id'

    @classmethod
    def create_job(cls, cursor, job: Job) -> None:
        cursor.execute(cls.insert(), (str(job.job_id), job.status.value))

    @classmethod
    def get_job(cls, cursor, job_id: UUID) -> Optional[Job]:
        cursor.execute(cls.get(), (str(job_id),))
        row = cursor.fetchone()
        if row is None:
            return None
        return Job(
            job_id=row[JobSchema.JOB_ID.name],
            status=JobStatus(row[JobSchema.STATUS.name]),
        )

    @classmethod
    def update_job_status(cls, cursor, job_id: UUID, status: JobStatus) -> None:
        cursor.execute(cls.modify(cls.SCHEMA.STATUS.name), (status.value, str(job_id)))
