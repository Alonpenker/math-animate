"""
ArtifactsRepository tests.

Uses FakeSqlCursor to verify that the repository builds correct SQL
and maps rows to Artifact domain objects correctly.
"""
from uuid import uuid4

from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.artifact import Artifact, ArtifactType

from tests.repositories.conftest import FakeSqlCursor


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_artifact(job_id=None) -> Artifact:
    return Artifact(
        artifact_id=uuid4(),
        job_id=job_id or uuid4(),
        artifact_type=ArtifactType.PYTHON_FILE,
        path="somejob/scene.py",
        size=512,
        sha256="deadbeef" * 8,
    )


def _artifact_row(artifact: Artifact) -> dict:
    return {
        "artifact_id": str(artifact.artifact_id),
        "job_id": str(artifact.job_id),
        "artifact_type": artifact.artifact_type.value,
        "path": artifact.path,
        "size": artifact.size,
        "sha256": artifact.sha256,
        "created_at": None,
        "updated_at": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ArtifactsRepository.create_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_create_artifact_executes_insert_with_correct_field_values():
    # Given
    cursor = FakeSqlCursor()
    artifact = _make_artifact()

    # When
    ArtifactsRepository.create_artifact(cursor, artifact)

    # Then
    assert len(cursor.queries) == 1
    _, params = cursor.queries[0]
    assert str(artifact.artifact_id) in params
    assert str(artifact.job_id) in params
    assert artifact.artifact_type.value in params
    assert artifact.path in params
    assert artifact.size in params
    assert artifact.sha256 in params


# ─────────────────────────────────────────────────────────────────────────────
# ArtifactsRepository.get_artifact_by_id
# ─────────────────────────────────────────────────────────────────────────────

def test_get_artifact_by_id_returns_artifact_when_row_exists():
    # Given
    artifact = _make_artifact()
    cursor = FakeSqlCursor(rows=[_artifact_row(artifact)])

    # When
    result = ArtifactsRepository.get_artifact_by_id(cursor, artifact.artifact_id)

    # Then
    assert result is not None
    assert result.artifact_id == artifact.artifact_id
    assert result.artifact_type == ArtifactType.PYTHON_FILE


def test_get_artifact_by_id_returns_none_when_no_row_found():
    # Given
    cursor = FakeSqlCursor(rows=[])

    # When
    result = ArtifactsRepository.get_artifact_by_id(cursor, uuid4())

    # Then
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# ArtifactsRepository.get_artifacts
# ─────────────────────────────────────────────────────────────────────────────

def test_get_artifacts_returns_all_artifacts_belonging_to_job():
    # Given
    job_id = uuid4()
    a1 = _make_artifact(job_id=job_id)
    a2 = _make_artifact(job_id=job_id)
    cursor = FakeSqlCursor(rows=[_artifact_row(a1), _artifact_row(a2)])

    # When
    results = ArtifactsRepository.get_artifacts(cursor, job_id)

    # Then
    assert len(results) == 2
    result_ids = {r.artifact_id for r in results}
    assert a1.artifact_id in result_ids
    assert a2.artifact_id in result_ids


# ─────────────────────────────────────────────────────────────────────────────
# ArtifactsRepository.delete_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_delete_artifact_returns_true_when_row_was_deleted():
    # Given
    cursor = FakeSqlCursor(rowcount=1)
    artifact_id = uuid4()

    # When
    result = ArtifactsRepository.delete_artifact(cursor, artifact_id)

    # Then
    assert result is True


def test_delete_artifact_returns_false_when_no_row_was_deleted():
    # Given
    cursor = FakeSqlCursor(rowcount=0)
    artifact_id = uuid4()

    # When
    result = ArtifactsRepository.delete_artifact(cursor, artifact_id)

    # Then
    assert result is False
