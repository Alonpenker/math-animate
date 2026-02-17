from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.artifact import Artifact, ArtifactType, ArtifactResponse
from app.schemas.jobs import Job
from app.domain.job_state import JobStatus


def _make_artifact(job_id, artifact_type=ArtifactType.PYTHON_FILE, **overrides):
    defaults = dict(
        artifact_id=uuid4(),
        job_id=job_id,
        artifact_type=artifact_type,
        path=f"{job_id}/file.{artifact_type.value}",
        size=100,
        sha256="a" * 64,
    )
    defaults.update(overrides)
    return Artifact(**defaults)


# ── list_artifacts ──────────────────────────────────────────────


def test_list_artifacts_returns_all(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    job_id = uuid4()
    a1 = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    a2 = _make_artifact(job_id, ArtifactType.MP4)
    test_store["artifacts"][a1.artifact_id] = a1
    test_store["artifacts"][a2.artifact_id] = a2

    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=None, cursor=fake_cursor
    )

    assert len(result) == 2
    assert all(isinstance(r, ArtifactResponse) for r in result)


def test_list_artifacts_filters_by_type(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    job_id = uuid4()
    py_artifact = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    mp4_artifact = _make_artifact(job_id, ArtifactType.MP4)
    test_store["artifacts"][py_artifact.artifact_id] = py_artifact
    test_store["artifacts"][mp4_artifact.artifact_id] = mp4_artifact

    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=ArtifactType.PYTHON_FILE, job_id=None, cursor=fake_cursor
    )

    assert len(result) == 1
    assert result[0].artifact_type == ArtifactType.PYTHON_FILE


def test_list_artifacts_filters_by_job_id(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    job_a = uuid4()
    job_b = uuid4()
    a1 = _make_artifact(job_a, ArtifactType.MP4)
    a2 = _make_artifact(job_b, ArtifactType.MP4)
    test_store["artifacts"][a1.artifact_id] = a1
    test_store["artifacts"][a2.artifact_id] = a2

    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=job_a, cursor=fake_cursor
    )

    assert len(result) == 1
    assert result[0].job_id == job_a


def test_list_artifacts_filters_by_type_and_job_id(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    job_id = uuid4()
    py = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    mp4 = _make_artifact(job_id, ArtifactType.MP4)
    other_job_py = _make_artifact(uuid4(), ArtifactType.PYTHON_FILE)
    test_store["artifacts"][py.artifact_id] = py
    test_store["artifacts"][mp4.artifact_id] = mp4
    test_store["artifacts"][other_job_py.artifact_id] = other_job_py

    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=ArtifactType.PYTHON_FILE, job_id=job_id, cursor=fake_cursor
    )

    assert len(result) == 1
    assert result[0].artifact_type == ArtifactType.PYTHON_FILE
    assert result[0].job_id == job_id


def test_list_artifacts_empty(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=None, cursor=fake_cursor
    )
    assert result == []


def test_list_artifacts_response_excludes_path(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    test_store["artifacts"][a.artifact_id] = a

    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=None, cursor=fake_cursor
    )

    assert len(result) == 1
    assert "path" not in type(result[0]).model_fields


# ── get_artifact ────────────────────────────────────────────────


def test_get_artifact_returns_metadata(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.MP4)
    test_store["artifacts"][a.artifact_id] = a

    result = artifacts_routes_with_mocks.get_artifact(a.artifact_id, cursor=fake_cursor)

    assert isinstance(result, ArtifactResponse)
    assert result.artifact_id == a.artifact_id
    assert result.artifact_type == ArtifactType.MP4
    assert result.size == a.size
    assert result.sha256 == a.sha256


def test_get_artifact_not_found_returns_404(
    artifacts_routes_with_mocks,
    fake_cursor,
):
    with pytest.raises(HTTPException) as exc_info:
        artifacts_routes_with_mocks.get_artifact(uuid4(), cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Artifact not found" in exc_info.value.detail


def test_get_artifact_response_excludes_path(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    test_store["artifacts"][a.artifact_id] = a

    result = artifacts_routes_with_mocks.get_artifact(a.artifact_id, cursor=fake_cursor)

    assert "path" not in type(result).model_fields


# ── download_artifact ───────────────────────────────────────────


def test_download_artifact_returns_file_response(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.PYTHON_FILE, path=f"{job_id}/code.py")
    test_store["artifacts"][a.artifact_id] = a
    test_store["objects"][a.path] = b"print('hello')"

    from fastapi.responses import FileResponse

    result = artifacts_routes_with_mocks.download_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    assert isinstance(result, FileResponse)
    assert result.filename == "code.py"
    assert result.media_type == "text/x-python"


def test_download_artifact_mp4_content_type(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.MP4, path=f"{job_id}/scene.mp4")
    test_store["artifacts"][a.artifact_id] = a
    test_store["objects"][a.path] = b"\x00\x00\x00\x1cftyp"

    result = artifacts_routes_with_mocks.download_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    assert result.media_type == "video/mp4"
    assert result.filename == "scene.mp4"


def test_download_artifact_not_found_returns_404(
    artifacts_routes_with_mocks,
    fake_cursor,
    mock_storage_service,
):
    with pytest.raises(HTTPException) as exc_info:
        artifacts_routes_with_mocks.download_artifact(
            uuid4(), cursor=fake_cursor, storage=mock_storage_service
        )

    assert exc_info.value.status_code == 404


# ── delete_artifact ─────────────────────────────────────────────


def test_delete_artifact_removes_from_store_and_storage(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.PYTHON_FILE, path=f"{job_id}/code.py")
    test_store["artifacts"][a.artifact_id] = a
    test_store["objects"][a.path] = b"print('hello')"

    result = artifacts_routes_with_mocks.delete_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    assert result is None  # 204 No Content
    assert a.artifact_id not in test_store["artifacts"]
    assert a.path not in test_store["objects"]


def test_delete_artifact_not_found_returns_404(
    artifacts_routes_with_mocks,
    fake_cursor,
    mock_storage_service,
):
    with pytest.raises(HTTPException) as exc_info:
        artifacts_routes_with_mocks.delete_artifact(
            uuid4(), cursor=fake_cursor, storage=mock_storage_service
        )

    assert exc_info.value.status_code == 404


def test_delete_artifact_succeeds_when_minio_file_already_gone(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    """Delete should succeed even if MinIO object was already removed externally."""
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.MP4, path=f"{job_id}/scene.mp4")
    test_store["artifacts"][a.artifact_id] = a
    # Intentionally NOT putting anything in test_store["objects"]

    result = artifacts_routes_with_mocks.delete_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    assert result is None
    assert a.artifact_id not in test_store["artifacts"]


# ── content_type mapping ────────────────────────────────────────


@pytest.mark.parametrize(
    "artifact_type, expected_content_type",
    [
        (ArtifactType.MP4, "video/mp4"),
        (ArtifactType.PYTHON_FILE, "text/x-python"),
        (ArtifactType.JSON, "application/json"),
        (ArtifactType.TXT, "text/plain"),
        (ArtifactType.LOG, "text/plain"),
        (ArtifactType.ZIP, "application/zip"),
        (ArtifactType.METADATA, "application/octet-stream"),
    ],
)
def test_artifact_type_content_type_mapping(artifact_type, expected_content_type):
    assert artifact_type.content_type == expected_content_type
