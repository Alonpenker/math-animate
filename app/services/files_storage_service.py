from minio import Minio
from uuid import UUID
from pathlib import Path

class FilesStorageService:
    
    def __init__(self, client: Minio, bucket: str):
        self._client = client
        self._bucket = bucket
    
    def save_artifact(self, job_id: UUID, file_path: Path) -> str:
        object_name = f"{job_id}/{file_path.name}"
        self._client.fput_object(self._bucket, object_name, str(file_path))
        return object_name

    def download_artifact(self, object_name: str, file_path: str) -> None:
        self._client.fget_object(self._bucket, object_name, file_path)

    def delete_artifact(self, object_name: str) -> None:
        self._client.remove_object(self._bucket, object_name)
