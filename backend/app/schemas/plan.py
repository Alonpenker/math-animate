from pydantic import BaseModel
from uuid import UUID

from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema
from app.schemas.video_plan import VideoPlan


class Plan(BaseModel):
    job_id: UUID
    plan: VideoPlan
    approved: bool

class PlanSchema(Schema):
    JOB_ID = DBColumn(name="job_id", type="UUID", attributes=["PRIMARY KEY"])
    PLAN = DBColumn(name="plan", type="TEXT", attributes=["NOT NULL"])
    APPROVED = DBColumn(name="approved", type="BOOLEAN", attributes=["NOT NULL","DEFAULT FALSE"])
