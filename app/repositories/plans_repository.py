from typing import Optional
from uuid import UUID

from app.dependencies.db import get_cursor
from app.schemas.video_plan import VideoPlan


class PlansRepository:
    
    def create_plan(
        self, job_id: UUID, plan: VideoPlan
    ) -> None:
        pass

    def get_plan(self, job_id: UUID) -> Optional[dict]:
        pass

    def approve_plan(self, job_id: UUID, approved: bool = True) -> Optional[dict]:
        pass
