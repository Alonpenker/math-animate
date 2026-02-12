from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from starlette.background import BackgroundTask
import tempfile
from uuid import UUID

from app.dependencies.db import get_cursor
from app.dependencies.storage import get_storage_service
from app.repositories.jobs_repository import JobsRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.services.files_storage_service import FilesStorageService
from app.repositories.plans_repository import PlansRepository
from app.schemas.jobs import *
from app.schemas.video_plan import VideoPlan
from app.schemas.user_request import UserRequest
from app.domain.job_state import JobStatus
from app.workers.runner import WorkerRunner

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("",response_model=JobResponse)
def create_job(user_request: UserRequest, cursor=Depends(get_cursor)) -> JobResponse:
    job = Job(status=JobStatus.CREATED)
    job_request = JobUserRequest(job=job, user_request=user_request)
    JobsRepository.create_job(cursor, job)
    WorkerRunner.advance(job_request)
    return JobResponse(job=job)


@router.get("/{job_id}/status",response_model=JobResponse)
def get_job_status(job_id: UUID, cursor=Depends(get_cursor)) -> JobResponse:
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found. (job_id={job_id})",
        )
    return JobResponse(job=job)


@router.get("/{job_id}/plan",response_model=JobResponse)
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


@router.patch("/{job_id}/approve",response_model=JobResponse)
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
        try:
            video_plan = VideoPlan.model_validate_json(plan.plan)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid stored plan JSON (job_id={job_id})",
            )
        job_request = JobPlanRequest(job=job, 
                                     plan=video_plan)
        WorkerRunner.advance(job_request)
    else:
        job = Job(job_id=job_id, status=JobStatus.CANCELLED)
        JobsRepository.update_job_status(cursor, job_id, JobStatus.CANCELLED)
    return JobResponse(job=job)


@router.get("/{job_id}/artifacts", response_model=JobResponse)
def get_artifacts(job_id: UUID, cursor=Depends(get_cursor)) -> JobResponse:
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found. (job_id={job_id})",
        )
    artifacts = ArtifactsRepository.get_artifacts(cursor, job_id)
    return JobResponse(job=job, data=artifacts)

@router.get("/{job_id}/artifacts/{artifact_id}")
def get_artifact(
    job_id: UUID,
    artifact_id: UUID,
    cursor=Depends(get_cursor),
    storage: FilesStorageService = Depends(get_storage_service),
) -> FileResponse:
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found. (job_id={job_id})",
        )
    artifact = ArtifactsRepository.get_artifact_by_id(cursor, artifact_id)
    if artifact is None or artifact.job_id != job_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found. (job_id={job_id}, artifact_id={artifact_id})",
        )
    
    file_name = Path(artifact.path).name
    with tempfile.NamedTemporaryFile(suffix=f"_{file_name}", delete=False) as tmp:
        dest_path = Path(tmp.name)
    storage.download_artifact(artifact.path, str(dest_path))
    return FileResponse(
        path=dest_path,
        filename=file_name,
        background=BackgroundTask(dest_path.unlink, missing_ok=True),
    )
