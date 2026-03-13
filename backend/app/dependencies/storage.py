from minio import Minio
from app.services.files_storage_service import FilesStorageService
from app.configs.app_settings import settings

_storage_client: Minio | None = None

def get_storage_client() -> Minio:
    global _storage_client
    if _storage_client is None:
        _storage_client = Minio(
            settings.storage_endpoint,
            access_key=settings.storage_access_key,
            secret_key=settings.storage_secret_key,
            secure=(settings.environment == "prod"),
        )
    return _storage_client

def init_storage() -> None:
    if settings.environment == "local":
        client = get_storage_client()
        if not client.bucket_exists(settings.storage_bucket):
            client.make_bucket(settings.storage_bucket)     

def get_storage_service() -> FilesStorageService:
    return FilesStorageService(
        client=get_storage_client(),
        bucket=settings.storage_bucket,
    )