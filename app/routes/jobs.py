from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID

from app.configs.limiter_config import LimitConfig
from app.dependencies.db import get_cursor
from app.dependencies.redis_client import get_redis_client
from app.dependencies.limiter import limiter
from app.repositories.jobs_repository import JobsRepository
from app.repositories.job_requests_repository import JobRequestsRepository
from app.repositories.plans_repository import PlansRepository
from app.schemas.jobs import *
from app.schemas.job_request import JobListResponse
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus
from app.workers.runner import WorkerRunner

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("",status_code=status.HTTP_201_CREATED)
@limiter.limit(LimitConfig.STRICT)
def create_job(
    user_request: UserRequest,
    redis_client=Depends(get_redis_client),
    cursor=Depends(get_cursor),
) -> JobResponse:
    job = Job(status=JobStatus.CREATED)
    job_request = JobUserRequest(job=job, user_request=user_request)
    JobsRepository.create_job(redis_client, job)
    JobRequestsRepository.create(cursor, job.job_id, user_request, JobStatus.CREATED)
    WorkerRunner.advance(job_request)
    return JobResponse(job=job)


@router.get("")
@limiter.limit(LimitConfig.NORMAL)
def get_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    topic: Optional[str] = None,
    job_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    cursor=Depends(get_cursor),
) -> JobListResponse:
    jobs, total = JobRequestsRepository.get_job_requests(
        cursor,
        page=page,
        page_size=page_size,
        topic=topic,
        job_id=job_id,
        status=status_filter,
    )
    return JobListResponse(
        jobs=jobs,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{job_id}/status")
@limiter.limit(LimitConfig.LIGHT)
def get_job_status(job_id: UUID, redis_client=Depends(get_redis_client)) -> JobResponse:
    job = JobsRepository.get_job(redis_client, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found. (job_id={job_id})",
        )
    return JobResponse(job=job)


@router.get("/{job_id}/plan")
@limiter.limit(LimitConfig.NORMAL)
def get_plan(job_id: UUID, redis_client=Depends(get_redis_client), cursor=Depends(get_cursor)) -> JobResponse:
    job = JobsRepository.get_job(redis_client, job_id)
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
@limiter.limit(LimitConfig.STRICT)
def approve_plan(job_id: UUID, approved: bool, redis_client=Depends(get_redis_client), cursor=Depends(get_cursor)) -> JobResponse:
    job = JobsRepository.get_job(redis_client, job_id)
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
        JobsRepository.update_job_status(redis_client, job_id, JobStatus.APPROVED)
        JobRequestsRepository.update_status(cursor, job_id, JobStatus.APPROVED)
        job_request = JobPlanRequest(job=job, plan=plan.plan)
        WorkerRunner.advance(job_request)
    else:
        job = Job(job_id=job_id, status=JobStatus.CANCELLED)
        JobsRepository.update_job_status(redis_client, job_id, JobStatus.CANCELLED)
        JobRequestsRepository.update_status(cursor, job_id, JobStatus.CANCELLED)
    return JobResponse(job=job)
