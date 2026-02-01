from minio import Minio
from uuid import UUID
from pathlib import Path

MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "artifacts"

# TODO: should transform into a more robust solution, so the worker/api intialize a connection once
# and then uses the same connection over and over
class FilesStorageService:
    def __init__(self) -> None:
        self._client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )
        if not self._client.bucket_exists(MINIO_BUCKET):
            self._client.make_bucket(MINIO_BUCKET)

    def save_artifact(self, job_id: UUID, file_path: str) -> str:
        object_name = f"{job_id}/{Path(file_path).name}"
        self._client.fput_object(MINIO_BUCKET, object_name, file_path)
        return object_name

    def download_artifact(self, object_name: str, file_path: str) -> None:
        self._client.fget_object(MINIO_BUCKET, object_name, file_path)
