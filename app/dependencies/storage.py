from minio import Minio
from app.services.files_storage_service import FilesStorageService
from app.configs.app_settings import settings

_minio_client: Minio | None = None

def get_storage_client() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.storage_access_point,
            access_key=settings.storage_access_point,
            secret_key=settings.storage_secret_key,
            secure=False,
        )
    return _minio_client

def init_storage() -> None:
    client = get_storage_client()
    if not client.bucket_exists(settings.storage_bucket):
        client.make_bucket(settings.storage_bucket)     

def get_storage_service() -> FilesStorageService:
    return FilesStorageService(
        client=get_storage_client(),
        bucket=settings.storage_bucket,
    )