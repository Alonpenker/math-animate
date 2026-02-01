from typing import Optional
from uuid import UUID

from app.schemas.jobs import Job
from app.domain.job_state import JobStatus
from app.repositories.repository import Repository

class JobsRepository(Repository):

    TABLE_NAME = 'jobs'
    COLUMNS = [("job_id","UUID PRIMARY KEY"),("status","TEXT")]
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
        return Job(job_id=UUID(row[0]), status=JobStatus(row[1]))

    @classmethod
    def update_job_status(cls, cursor, job_id: UUID, status: str) -> None:
        FIELD = "status"
        cursor.execute(cls.modify(FIELD), (status, str(job_id)))
