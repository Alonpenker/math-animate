from typing import Optional
from uuid import UUID

from app.schemas.video_plan import VideoPlan


class PlansRepository:
    
    @staticmethod
    def _verify_table(cursor) -> None:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS plans (job_id TEXT PRIMARY KEY, plan_json TEXT)"
        )
    
    @staticmethod
    def create_plan(
        cursor, job_id: UUID, plan: VideoPlan
    ) -> None:
        PlansRepository._verify_table(cursor)
        cursor.execute(
            "INSERT INTO plans (job_id, plan_json) VALUES (%s, %s)",
            (str(job_id), plan.model_dump_json()),
        )

    @staticmethod
    def get_plan(cursor, job_id: UUID) -> None:
        pass

    @staticmethod
    def approve_plan(cursor, job_id: UUID, approved: bool = True) -> None:
        pass
