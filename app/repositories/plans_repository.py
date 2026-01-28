from typing import Optional
from uuid import UUID

from app.schemas.video_plan import VideoPlan


class PlansRepository:
    
    @staticmethod
    def _verify_table(cursor) -> None:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS plans (job_id TEXT PRIMARY KEY, plan_json TEXT, approved BOOLEAN DEFAULT FALSE)"
        )
    
    @staticmethod
    def create_plan(
        cursor, job_id: UUID, plan: VideoPlan
    ) -> None:
        PlansRepository._verify_table(cursor)
        cursor.execute(
            "INSERT INTO plans (job_id, plan_json, approved) VALUES (%s, %s, %s)",
            (str(job_id), plan.model_dump_json(), False),
        )

    @staticmethod
    def get_plan(cursor, job_id: UUID) -> Optional[VideoPlan]:
        PlansRepository._verify_table(cursor)
        cursor.execute(
            "SELECT plan_json FROM plans WHERE job_id = %s",
            (str(job_id),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return VideoPlan.model_validate_json(row[0])

    @staticmethod
    def approve_plan(cursor, job_id: UUID, approved: bool = True) -> Optional[VideoPlan]:
        PlansRepository._verify_table(cursor)
        cursor.execute(
            "UPDATE plans SET approved = %s WHERE job_id = %s",
            (approved, str(job_id)),
        )
        return PlansRepository.get_plan(cursor,job_id)
