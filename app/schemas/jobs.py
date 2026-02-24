from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4, UUID

from app.schemas.video_plan import VideoPlan
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus
from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema

class Job(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    status: JobStatus

class JobRequest(BaseModel):
    job: Job

class JobUserRequest(JobRequest):
    user_request: UserRequest
    
class JobPlanRequest(JobRequest):
    plan: VideoPlan

class JobCodeRequest(JobRequest):
    code: str
    is_retry: bool = False

class JobFixRequest(JobRequest):
    code: str
    error_context: str

class JobResponse(BaseModel):
    job: Job
    data: Optional[Any] = None

class JobSchema(Schema):
    JOB_ID = DBColumn(name="job_id", type="UUID", attributes=["PRIMARY KEY"])
    STATUS = DBColumn(name="status", type="TEXT", attributes=["NOT NULL"])
