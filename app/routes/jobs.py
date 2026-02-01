from fastapi import APIRouter, Depends, HTTPException
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
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
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
    job = JobsRepository.get_job(cursor, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    artifacts = ArtifactsRepository.get_artifacts(cursor, job_id)
    if not artifacts:
        raise HTTPException(status_code=404, detail="Artifacts not found")
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
        raise HTTPException(status_code=404, detail="Job not found")
    artifact = ArtifactsRepository.get_artifact_by_id(cursor, artifact_id)
    if artifact is None or artifact.job_id != job_id:
        raise HTTPException(status_code=404, detail="Artifact not found")
    file_name = Path(artifact.path).name
    with tempfile.NamedTemporaryFile(prefix="artifact_", suffix=f"_{file_name}", delete=False) as tmp:
        dest_path = Path(tmp.name)
    storage.download_artifact(artifact.path, str(dest_path))
    return FileResponse(
        path=dest_path,
        filename=file_name,
        background=BackgroundTask(dest_path.unlink, missing_ok=True),
    )
