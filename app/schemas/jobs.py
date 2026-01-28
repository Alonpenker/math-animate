from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4, UUID

from app.schemas.artifact import Artifact
from app.schemas.video_plan import VideoPlan
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus

class Job(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    status: JobStatus

class JobRequest(Job):
    pass

class JobUserRequest(JobRequest):
    data: UserRequest
    
class JobPlanRequest(JobRequest):
    data: VideoPlan

class JobResponse(BaseModel):
    job: Job
    data: Optional[VideoPlan | List[Artifact]] = None
