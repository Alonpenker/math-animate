from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from app.domain.job_state import JobStatus
from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema
from app.schemas.user_request import UserRequest


class JobRequestSchema(Schema):
    JOB_ID = DBColumn(name="job_id", type="UUID", attributes=["PRIMARY KEY"])
    TOPIC = DBColumn(name="topic", type="TEXT", attributes=["NOT NULL"])
    MISCONCEPTIONS = DBColumn(name="misconceptions", type="TEXT[]", attributes=["NOT NULL", "DEFAULT '{}'"])
    CONSTRAINTS = DBColumn(name="constraints", type="TEXT[]", attributes=["NOT NULL", "DEFAULT '{}'"])
    EXAMPLES = DBColumn(name="examples", type="TEXT[]", attributes=["NOT NULL", "DEFAULT '{}'"])
    NUMBER_OF_SCENES = DBColumn(name="number_of_scenes", type="INTEGER", attributes=["NOT NULL"])
    STATUS = DBColumn(name="status", type="TEXT", attributes=["NOT NULL"])


class JobListItem(UserRequest):
    job_id: UUID
    status: JobStatus
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    jobs: list[JobListItem]
    total: int
    page: int
    page_size: int
