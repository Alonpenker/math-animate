from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4, UUID

from app.schemas.video_plan import VideoPlan
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus

class Job(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    status: JobStatus

class JobRequest(BaseModel):
    job: Job

class JobUserRequest(JobRequest):
    user_request: UserRequest
    
class JobPlanRequest(JobRequest):
    plan: VideoPlan

class JobFixAttemptRequest(JobRequest):
    fix_attempt: int = Field(default=0, ge=0)

class JobCodeRequest(JobFixAttemptRequest):
    code: str

class JobFixRequest(JobFixAttemptRequest):
    code: str
    error_context: str

class JobResponse(BaseModel):
    job: Job
    data: Optional[Any] = None
