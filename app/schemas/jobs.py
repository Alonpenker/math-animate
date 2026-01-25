from typing import List, Optional

from pydantic import BaseModel

from app.schemas.artifact import Artifact
from app.schemas.video_plan import VideoPlan
from domain.job_state import JobStatus

class JobData(BaseModel):
    job_id: str
    status: JobStatus

class JobResponse(BaseModel):
    job_data: JobData
    data: Optional[List[VideoPlan] | List[Artifact]] = None