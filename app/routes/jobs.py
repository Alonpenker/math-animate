from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.dependencies.db import get_cursor
from app.dependencies.storage import get_storage_service
from app.repositories.jobs_repository import JobsRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.services.files_storage_service import FilesStorageService
from app.schemas.artifact import Artifact, ArtifactType
from app.repositories.plans_repository import PlansRepository
from app.schemas.jobs import *
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus
from app.workers.runner import WorkerRunner

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("",response_model=JobResponse)
def create_job(user_request: UserRequest, cursor=Depends(get_cursor)) -> JobResponse:
    job = Job(status=JobStatus.CREATED)
    job_request = JobUserRequest(job_id=job.job_id, status=job.status, data=user_request)
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
def get_plan(job_id: UUID, cursor=Depends(get_cursor)) -> JobResponse:
    plan = PlansRepository.get_plan(cursor, job_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    job = Job(job_id=job_id, status=JobStatus.PLANNED)
    return JobResponse(job=job, data=plan)


@router.patch("/{job_id}/approve",response_model=JobResponse)
def approve_plan(job_id: UUID, approved: bool, cursor=Depends(get_cursor)) -> JobResponse:
    plan = PlansRepository.approve_plan(cursor, job_id, approved)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    if approved:
        job = Job(job_id=job_id, status=JobStatus.APPROVED)
        JobsRepository.update_job_status(cursor, job_id, JobStatus.APPROVED.value)
        job_request = JobPlanRequest(job_id=job.job_id, status=job.status, data=plan)
        WorkerRunner.advance(job_request)
    else:
        job = Job(job_id=job_id, status=JobStatus.CANCELLED)
        JobsRepository.update_job_status(cursor, job_id, JobStatus.CANCELLED.value)
    return JobResponse(job=job, data=plan)


@router.get("/{job_id}/artifacts", response_model=JobResponse)
def get_artifacts(job_id: UUID, cursor=Depends(get_cursor)) -> JobResponse:
    job_row = JobsRepository.get_job(cursor, job_id)
    if job_row is None:
        raise HTTPException(status_code=404, detail="Job not found")
    artifacts = ArtifactsRepository.get_artifacts(cursor, job_id)
    if artifacts is None:
        raise HTTPException(status_code=404, detail="Artifacts not found")
    job = Job(job_id=UUID(job_row["job_id"]), status=JobStatus(job_row["status"]))
    artifact_list = [
        Artifact(
            job_id=job_id,
            artifact_type=ArtifactType(item["artifact_type"]),
            path=item["path"],
            size=item["size"],
            sha256=item["sha256"],
        )
        for item in artifacts
    ]
    return JobResponse(job=job, data=artifact_list)

# TODO: learn how to retrieve files using the api from the minio
# TODO: implement the get specific artifact logic (need to add artifact_id apperently)
@router.get("/{job_id}/artifacts/{artifact_id}")
def get_artifact(job_id: str, artifact_id: str, storage: FilesStorageService = Depends(get_storage_service)) -> None:
    # Get specific artifact logic...
    pass
