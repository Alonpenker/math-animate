from fastapi import APIRouter

from app.schemas.jobs import JobData, JobResponse
from app.schemas.user_request import UserRequest
from domain.job_state import JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("",response_model=JobResponse)
def create_job(user_request: UserRequest) -> JobResponse:
    job_id = "job_placeholder"
    # Job creation logic...
    job_data = JobData(job_id=job_id, status=JobStatus.CREATED)
    return JobResponse(job_data=job_data)


@router.get("/{job_id}",response_model=JobResponse)
def get_job_status(job_id: str) -> JobResponse:
    # Job checking logic...
    job_data = JobData(job_id="123",status=JobStatus.APPROVED)
    return JobResponse(job_data=job_data)


@router.get("/{job_id}/plan",response_model=JobResponse)
def get_plan(job_id: str) -> JobResponse:
    # Get plan logic...
    job_data = JobData(job_id=job_id,status=JobStatus.PLANNED)
    return JobResponse(job_data=job_data)


@router.post("/{job_id}/approve",response_model=JobResponse)
def approve_plan(job_id: str, approved: bool) -> JobResponse:
    if approved:
        # Approved plan logic...
        job_data = JobData(job_id=job_id,status=JobStatus.APPROVED)
    else:
        # not approved plan logic...
        job_data = JobData(job_id=job_id,status=JobStatus.CANCELLED)
    return JobResponse(job_data=job_data)


@router.get("/{job_id}/artifacts", response_model=JobResponse)
def get_artifacts(job_id: str) -> JobResponse:
    # Get artifacts logic...
    job_data = JobData(job_id=job_id,status=JobStatus.CANCELLED)
    return JobResponse(job_data=job_data)


@router.get("/{job_id}/artifacts/{artifact_id}")
def get_artifact(job_id: str, artifact_id: str) -> None:
    # Get specific artifact logic...
    pass
