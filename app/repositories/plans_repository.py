from typing import Optional
from uuid import UUID

from app.schemas.video_plan import VideoPlan
from app.repositories.repository import Repository


class PlansRepository(Repository):

    TABLE_NAME = 'plans'
    COLUMNS = [("job_id","UUID PRIMARY KEY"),("plan_json","TEXT"),("approved","BOOLEAN DEFAULT FALSE")]
    PRIMARY_KEY = 'job_id'
    
    @classmethod
    def create_plan(cls,
        cursor, job_id: UUID, plan: VideoPlan
    ) -> None:
        cursor.execute(cls.insert(), (str(job_id), plan.model_dump_json(), False))

    @classmethod
    def get_plan(cls, cursor, job_id: UUID) -> Optional[VideoPlan]:
        cursor.execute(cls.get(), (str(job_id),))
        row = cursor.fetchone()
        if row is None:
            return None
        return VideoPlan.model_validate_json(row[0])

    @classmethod
    def approve_plan(cls,cursor, job_id: UUID, approved: bool = True) -> Optional[VideoPlan]:
        FIELD = "plan_json"
        cursor.execute(cls.modify(FIELD), (approved, str(job_id)))
        return PlansRepository.get_plan(cursor,job_id)
