from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.dependencies.db import get_cursor
from app.repositories.jobs_repository import JobsRepository
from app.repositories.plans_repository import PlansRepository
from app.schemas.jobs import *
from app.schemas.video_plan import VideoPlan
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus
from app.workers.runner import WorkerRunner

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("",status_code=status.HTTP_201_CREATED)
def create_job(user_request: UserRequest, cursor=Depends(get_cursor)) -> JobResponse:
    job = Job(status=JobStatus.CREATED)
    job_request = JobUserRequest(job=job, user_request=user_request)
    JobsRepository.create_job(cursor, job)
    WorkerRunner.advance(job_request)
    return JobResponse(job=job)


@router.get("/{job_id}/status")
def get_job_status(job_id: UUID, cursor=Depends(get_cursor)) -> JobResponse:
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found. (job_id={job_id})",
        )
    return JobResponse(job=job)


@router.get("/{job_id}/plan")
def get_plan(job_id: UUID, cursor=Depends(get_cursor)) -> JobResponse:
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found. (job_id={job_id})",
        )
    plan = PlansRepository.get_plan(cursor, job_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found for this job. (job_id={job_id})",
        )
    job = Job(job_id=job_id, status=job.status)
    return JobResponse(job=job, data=plan)


@router.patch("/{job_id}/approve")
def approve_plan(job_id: UUID, approved: bool, cursor=Depends(get_cursor)) -> JobResponse:
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found. (job_id={job_id})",
        )
    if job.status != JobStatus.PLANNED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid state for approval. (job_id={job_id}, status={job.status.value})",
        )
    plan = PlansRepository.approve_plan(cursor, job_id, approved)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan not found for this job. (job_id={job_id})",
        )
    if approved:
        job = Job(job_id=job_id, status=JobStatus.APPROVED)
        JobsRepository.update_job_status(cursor, job_id, JobStatus.APPROVED)
        job_request = JobPlanRequest(job=job, plan=plan.plan)
        WorkerRunner.advance(job_request)
    else:
        job = Job(job_id=job_id, status=JobStatus.CANCELLED)
        JobsRepository.update_job_status(cursor, job_id, JobStatus.CANCELLED)
    return JobResponse(job=job)
