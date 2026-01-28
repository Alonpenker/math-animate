from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.dependencies.db import get_cursor
from app.repositories.jobs_repository import JobsRepository
from app.schemas.jobs import Job, JobRequest, JobResponse
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus
from app.workers.runner import WorkerRunner

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("",response_model=JobResponse)
def create_job(user_request: UserRequest, cursor=Depends(get_cursor)) -> JobResponse:
    job = Job(status=JobStatus.CREATED)
    job_request = JobRequest(job_id=job.job_id, status=job.status, data=user_request)
    JobsRepository.create_job(cursor, job)
    WorkerRunner.advance(job_request)
    return JobResponse(job=job)


@router.get("/{job_id}",response_model=JobResponse)
def get_job_status(job_id: UUID, cursor=Depends(get_cursor)) -> JobResponse:
    job_row = JobsRepository.get_job(cursor, job_id)
    if job_row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job = Job(job_id=UUID(job_row["job_id"]), status=JobStatus(job_row["status"]))
    return JobResponse(job=job)


@router.get("/{job_id}/plan",response_model=JobResponse)
def get_plan(job_id: str) -> JobResponse:
    # Get plan logic...
    job = Job(job_id=UUID(job_id),status=JobStatus.PLANNED)
    return JobResponse(job=job)


@router.post("/{job_id}/approve",response_model=JobResponse)
def approve_plan(job_id: str, approved: bool) -> JobResponse:
    if approved:
        # Approved plan logic...
        job = Job(job_id=UUID(job_id),status=JobStatus.APPROVED)
    else:
        # not approved plan logic...
        job = Job(job_id=UUID(job_id),status=JobStatus.CANCELLED)
    return JobResponse(job=job)


@router.get("/{job_id}/artifacts", response_model=JobResponse)
def get_artifacts(job_id: str) -> JobResponse:
    # Get artifacts logic...
    job = Job(job_id=UUID(job_id),status=JobStatus.CANCELLED)
    return JobResponse(job=job)


@router.get("/{job_id}/artifacts/{artifact_id}")
def get_artifact(job_id: str, artifact_id: str) -> None:
    # Get specific artifact logic...
    pass
