from typing import Optional
from uuid import UUID

from app.schemas.video_plan import VideoPlan
from app.repositories.repository import Repository
from app.schemas.plan import PlanSchema, Plan


class PlansRepository(Repository):

    TABLE_NAME = 'plans'
    SCHEMA = PlanSchema
    PRIMARY_KEY = 'job_id'
    
    @classmethod
    def create_plan(cls,
        cursor, job_id: UUID, plan: VideoPlan
    ) -> None:
        cursor.execute(cls.insert(), (str(job_id), plan.model_dump_json(), False))

    @classmethod
    def get_plan(cls, cursor, job_id: UUID) -> Optional[Plan]:
        cursor.execute(cls.get(), (str(job_id),))
        row = cursor.fetchone()
        if row is None:
            return None
        return Plan(
            job_id=row[PlanSchema.JOB_ID.name],
            plan=row[PlanSchema.PLAN.name],
            approved=row[PlanSchema.APPROVED.name],
        )

    @classmethod
    def approve_plan(cls,cursor, job_id: UUID, approved: bool = True) -> Optional[Plan]:
        cursor.execute(cls.modify(cls.SCHEMA.APPROVED.name), (approved, str(job_id)))
        return PlansRepository.get_plan(cursor,job_id)
