from typing import Optional
from uuid import UUID

from app.schemas.jobs import Job

class JobsRepository:
    
    @staticmethod
    def _verify_table(cursor) -> None:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, status TEXT)"
        )
    
    @staticmethod
    def create_job(
        cursor, job: Job
    ) -> None:
        JobsRepository._verify_table(cursor)
        cursor.execute(
            "INSERT INTO jobs (job_id, status) VALUES (%s, %s)",
            (str(job.job_id), job.status.value),
        )

    @staticmethod
    def get_job(cursor, job_id: UUID) -> Optional[dict]:
        JobsRepository._verify_table(cursor)
        cursor.execute(
            "SELECT job_id, status FROM jobs WHERE job_id = %s",
            (str(job_id),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {"job_id": row[0], "status": row[1]}

    @staticmethod
    def update_job_status(cursor, job_id: UUID, status: str) -> None:
        JobsRepository._verify_table(cursor)
        cursor.execute(
            "UPDATE jobs SET status = %s WHERE job_id = %s",
            (status, str(job_id)),
        )
