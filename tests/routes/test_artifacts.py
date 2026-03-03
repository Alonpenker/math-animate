from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.schemas.artifact import Artifact, ArtifactType, ArtifactResponse


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


# ─────────────────────────────────────────────────────────────────────────────
# list_artifacts
# ─────────────────────────────────────────────────────────────────────────────

def test_list_artifacts_returns_all_when_no_filters_applied(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    job_id = uuid4()
    a1 = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    a2 = _make_artifact(job_id, ArtifactType.MP4)
    test_store["artifacts"][a1.artifact_id] = a1
    test_store["artifacts"][a2.artifact_id] = a2

    # When
    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=None, cursor=fake_cursor
    )

    # Then
    assert len(result) == 2
    assert all(isinstance(r, ArtifactResponse) for r in result)


def test_list_artifacts_returns_only_matching_type_when_type_filter_provided(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    job_id = uuid4()
    py = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    mp4 = _make_artifact(job_id, ArtifactType.MP4)
    test_store["artifacts"][py.artifact_id] = py
    test_store["artifacts"][mp4.artifact_id] = mp4

    # When
    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=ArtifactType.PYTHON_FILE, job_id=None, cursor=fake_cursor
    )

    # Then
    assert len(result) == 1
    assert result[0].artifact_type == ArtifactType.PYTHON_FILE


def test_list_artifacts_returns_only_matching_job_when_job_filter_provided(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    job_a, job_b = uuid4(), uuid4()
    a1 = _make_artifact(job_a, ArtifactType.MP4)
    a2 = _make_artifact(job_b, ArtifactType.MP4)
    test_store["artifacts"][a1.artifact_id] = a1
    test_store["artifacts"][a2.artifact_id] = a2

    # When
    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=job_a, cursor=fake_cursor
    )

    # Then
    assert len(result) == 1
    assert result[0].job_id == job_a


def test_list_artifacts_applies_both_type_and_job_id_filters_simultaneously(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    job_id = uuid4()
    py = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    mp4 = _make_artifact(job_id, ArtifactType.MP4)
    other_job_py = _make_artifact(uuid4(), ArtifactType.PYTHON_FILE)
    test_store["artifacts"][py.artifact_id] = py
    test_store["artifacts"][mp4.artifact_id] = mp4
    test_store["artifacts"][other_job_py.artifact_id] = other_job_py

    # When
    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=ArtifactType.PYTHON_FILE, job_id=job_id, cursor=fake_cursor
    )

    # Then
    assert len(result) == 1
    assert result[0].artifact_type == ArtifactType.PYTHON_FILE
    assert result[0].job_id == job_id


def test_list_artifacts_returns_empty_list_when_no_artifacts_exist(
    artifacts_routes_with_mocks,
    fake_cursor,
):
    # Given — empty store

    # When
    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=None, cursor=fake_cursor
    )

    # Then
    assert result == []


def test_list_artifacts_response_does_not_expose_storage_path(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.PYTHON_FILE)
    test_store["artifacts"][a.artifact_id] = a

    # When
    result = artifacts_routes_with_mocks.list_artifacts(
        artifact_type=None, job_id=None, cursor=fake_cursor
    )

    # Then
    assert "path" not in type(result[0]).model_fields


# ─────────────────────────────────────────────────────────────────────────────
# get_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_get_artifact_returns_metadata_for_existing_artifact(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    a = _make_artifact(uuid4(), ArtifactType.MP4)
    test_store["artifacts"][a.artifact_id] = a

    # When
    result = artifacts_routes_with_mocks.get_artifact(a.artifact_id, cursor=fake_cursor)

    # Then
    assert isinstance(result, ArtifactResponse)
    assert result.artifact_id == a.artifact_id
    assert result.artifact_type == ArtifactType.MP4
    assert result.size == a.size
    assert result.sha256 == a.sha256


def test_get_artifact_raises_404_when_artifact_not_found(
    artifacts_routes_with_mocks,
    fake_cursor,
):
    # Given
    missing_id = uuid4()

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        artifacts_routes_with_mocks.get_artifact(missing_id, cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Artifact not found" in exc_info.value.detail


def test_get_artifact_response_does_not_expose_storage_path(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    a = _make_artifact(uuid4(), ArtifactType.PYTHON_FILE)
    test_store["artifacts"][a.artifact_id] = a

    # When
    result = artifacts_routes_with_mocks.get_artifact(a.artifact_id, cursor=fake_cursor)

    # Then
    assert "path" not in type(result).model_fields


# ─────────────────────────────────────────────────────────────────────────────
# download_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_download_artifact_returns_file_response_with_correct_filename_and_media_type(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    # Given
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.PYTHON_FILE, path=f"{job_id}/code.py")
    test_store["artifacts"][a.artifact_id] = a
    test_store["objects"][a.path] = b"print('hello')"

    # When
    result = artifacts_routes_with_mocks.download_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    # Then
    assert isinstance(result, FileResponse)
    assert result.filename == "code.py"
    assert result.media_type == "text/x-python"


def test_download_artifact_uses_video_mp4_media_type_for_mp4_artifacts(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    # Given
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.MP4, path=f"{job_id}/scene.mp4")
    test_store["artifacts"][a.artifact_id] = a
    test_store["objects"][a.path] = b"\x00\x00\x00\x1cftyp"

    # When
    result = artifacts_routes_with_mocks.download_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    # Then
    assert result.media_type == "video/mp4"
    assert result.filename == "scene.mp4"


def test_download_artifact_raises_404_when_artifact_not_found(
    artifacts_routes_with_mocks,
    fake_cursor,
    mock_storage_service,
):
    # Given
    missing_id = uuid4()

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        artifacts_routes_with_mocks.download_artifact(
            missing_id, cursor=fake_cursor, storage=mock_storage_service
        )

    assert exc_info.value.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# delete_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_delete_artifact_removes_record_from_store_and_storage(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    # Given
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.PYTHON_FILE, path=f"{job_id}/code.py")
    test_store["artifacts"][a.artifact_id] = a
    test_store["objects"][a.path] = b"print('hello')"

    # When
    result = artifacts_routes_with_mocks.delete_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    # Then
    assert result is None  # HTTP 204 No Content
    assert a.artifact_id not in test_store["artifacts"]
    assert a.path not in test_store["objects"]


def test_delete_artifact_raises_404_when_artifact_not_found(
    artifacts_routes_with_mocks,
    fake_cursor,
    mock_storage_service,
):
    # Given
    missing_id = uuid4()

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        artifacts_routes_with_mocks.delete_artifact(
            missing_id, cursor=fake_cursor, storage=mock_storage_service
        )

    assert exc_info.value.status_code == 404


def test_delete_artifact_succeeds_even_when_minio_object_already_missing(
    artifacts_routes_with_mocks,
    fake_cursor,
    test_store,
    mock_storage_service,
):
    # Given
    job_id = uuid4()
    a = _make_artifact(job_id, ArtifactType.MP4, path=f"{job_id}/scene.mp4")
    test_store["artifacts"][a.artifact_id] = a
    # Intentionally NOT putting the file in test_store["objects"]

    # When
    result = artifacts_routes_with_mocks.delete_artifact(
        a.artifact_id, cursor=fake_cursor, storage=mock_storage_service
    )

    # Then
    assert result is None
    assert a.artifact_id not in test_store["artifacts"]


# ─────────────────────────────────────────────────────────────────────────────
# ArtifactType.content_type mapping
# ─────────────────────────────────────────────────────────────────────────────

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
def test_artifact_type_has_correct_content_type_mapping(artifact_type, expected_content_type):
    # Given — artifact_type enum value

    # When
    content_type = artifact_type.content_type

    # Then
    assert content_type == expected_content_type
