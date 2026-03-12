"""
FilesStorageService tests.

Uses a fake Minio client to verify object storage operations without any
real network or MinIO instance.
"""
from pathlib import Path
from uuid import uuid4

from app.services.files_storage_service import FilesStorageService


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class FakeMinioClient:
    """Records every call made so tests can assert on exact arguments."""

    def __init__(self):
        self.fput_calls: list[tuple[str, str, str]] = []
        self.fget_calls: list[tuple[str, str, str]] = []
        self.remove_calls: list[tuple[str, str]] = []

    def fput_object(self, bucket: str, object_name: str, file_path: str) -> None:
        self.fput_calls.append((bucket, object_name, file_path))

    def fget_object(self, bucket: str, object_name: str, file_path: str) -> None:
        self.fget_calls.append((bucket, object_name, file_path))

    def remove_object(self, bucket: str, object_name: str) -> None:
        self.remove_calls.append((bucket, object_name))


# ─────────────────────────────────────────────────────────────────────────────
# FilesStorageService.save_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_save_artifact_returns_object_name_with_job_id_prefix():
    # Given
    client = FakeMinioClient()
    service = FilesStorageService(client, "my-bucket")
    job_id = uuid4()
    file_path = Path("/tmp/abc123.py")

    # When
    result = service.save_artifact(job_id, file_path)

    # Then
    assert result == f"{job_id}/abc123.py"


def test_save_artifact_uploads_to_correct_bucket_and_path():
    # Given
    client = FakeMinioClient()
    service = FilesStorageService(client, "my-bucket")
    job_id = uuid4()
    file_path = Path("/tmp/scene.py")

    # When
    service.save_artifact(job_id, file_path)

    # Then
    assert len(client.fput_calls) == 1
    bucket, object_name, path_str = client.fput_calls[0]
    assert bucket == "my-bucket"
    assert object_name == f"{job_id}/scene.py"
    assert path_str == str(file_path)


# ─────────────────────────────────────────────────────────────────────────────
# FilesStorageService.download_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_download_artifact_calls_fget_with_bucket_and_paths():
    # Given
    client = FakeMinioClient()
    service = FilesStorageService(client, "my-bucket")

    # When
    service.download_artifact("job123/scene.py", "/local/scene.py")

    # Then
    assert client.fget_calls == [("my-bucket", "job123/scene.py", "/local/scene.py")]


# ─────────────────────────────────────────────────────────────────────────────
# FilesStorageService.delete_artifact
# ─────────────────────────────────────────────────────────────────────────────

def test_delete_artifact_calls_remove_with_bucket_and_object_name():
    # Given
    client = FakeMinioClient()
    service = FilesStorageService(client, "my-bucket")

    # When
    service.delete_artifact("job123/scene.py")

    # Then
    assert client.remove_calls == [("my-bucket", "job123/scene.py")]
