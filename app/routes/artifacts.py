from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
from starlette.background import BackgroundTask
import tempfile
from typing import List, Optional
from uuid import UUID

from app.configs.limiter_config import LimitConfig
from app.dependencies.db import get_cursor
from app.dependencies.limiter import limiter
from app.dependencies.storage import get_storage_service
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.artifact import ArtifactType, ArtifactResponse
from app.services.files_storage_service import FilesStorageService

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.get("", response_model=List[ArtifactResponse])
@limiter.limit(LimitConfig.NORMAL)
def list_artifacts(
    artifact_type: Optional[ArtifactType] = None,
    job_id: Optional[UUID] = None,
    cursor=Depends(get_cursor),
) -> List[ArtifactResponse]:
    artifacts = ArtifactsRepository.get_all_artifacts(
        cursor,
        artifact_type=artifact_type,
        job_id=job_id,
    )
    return [
        ArtifactResponse(
            artifact_id=a.artifact_id,
            job_id=a.job_id,
            artifact_type=a.artifact_type,
            size=a.size,
            sha256=a.sha256,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in artifacts
    ]


@router.get("/{artifact_id}", response_model=ArtifactResponse)
@limiter.limit(LimitConfig.NORMAL)
def get_artifact(
    artifact_id: UUID,
    cursor=Depends(get_cursor),
) -> ArtifactResponse:
    artifact = ArtifactsRepository.get_artifact_by_id(cursor, artifact_id)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found. (artifact_id={artifact_id})",
        )
    return ArtifactResponse(
        artifact_id=artifact.artifact_id,
        job_id=artifact.job_id,
        artifact_type=artifact.artifact_type,
        size=artifact.size,
        sha256=artifact.sha256,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.get("/{artifact_id}/download")
@limiter.limit(LimitConfig.STRICT)
def download_artifact(
    artifact_id: UUID,
    cursor=Depends(get_cursor),
    storage: FilesStorageService = Depends(get_storage_service),
) -> FileResponse:
    artifact = ArtifactsRepository.get_artifact_by_id(cursor, artifact_id)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found. (artifact_id={artifact_id})",
        )

    file_name = Path(artifact.path).name
    with tempfile.NamedTemporaryFile(suffix=f"_{file_name}", delete=False) as tmp:
        dest_path = Path(tmp.name)
    storage.download_artifact(artifact.path, str(dest_path))

    return FileResponse(
        path=dest_path,
        filename=file_name,
        media_type=artifact.artifact_type.content_type,
        background=BackgroundTask(dest_path.unlink, missing_ok=True),
    )


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(LimitConfig.STRICT)
def delete_artifact(
    artifact_id: UUID,
    cursor=Depends(get_cursor),
    storage: FilesStorageService = Depends(get_storage_service),
) -> None:
    artifact = ArtifactsRepository.get_artifact_by_id(cursor, artifact_id)
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found. (artifact_id={artifact_id})",
        )

    try:
        storage.delete_artifact(artifact.path)
    except Exception:
        pass

    ArtifactsRepository.delete_artifact(cursor, artifact_id)
