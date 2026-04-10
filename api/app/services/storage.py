import io
from typing import BinaryIO
from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.S3_ENDPOINT,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_USE_SSL,
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        buckets = [
            settings.S3_BUCKET_RAW,
            settings.S3_BUCKET_PROCESSED,
            settings.S3_BUCKET_CLIPS,
            settings.S3_BUCKET_THUMBNAILS,
        ]
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info("Created bucket", bucket=bucket)
            except S3Error as e:
                logger.error("Failed to create bucket", bucket=bucket, error=str(e))

    async def upload_file(self, file: UploadFile, path: str, bucket: str = None):
        bucket = bucket or settings.S3_BUCKET_RAW
        content = await file.read()
        self.client.put_object(
            bucket, path,
            io.BytesIO(content),
            length=len(content),
            content_type=file.content_type or "application/octet-stream",
        )
        logger.info("Uploaded file", path=path, bucket=bucket, size=len(content))
        return path

    def upload_bytes(self, data: bytes, path: str, bucket: str = None, content_type: str = "application/octet-stream"):
        bucket = bucket or settings.S3_BUCKET_PROCESSED
        self.client.put_object(
            bucket, path,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return path

    def download_file(self, path: str, bucket: str = None) -> bytes:
        bucket = bucket or settings.S3_BUCKET_RAW
        response = self.client.get_object(bucket, path)
        data = response.read()
        response.close()
        response.release_conn()
        return data

    def download_to_file(self, path: str, local_path: str, bucket: str = None):
        bucket = bucket or settings.S3_BUCKET_RAW
        self.client.fget_object(bucket, path, local_path)
        return local_path

    async def get_presigned_url(self, path: str, bucket: str = None, expires_hours: int = 24) -> str:
        bucket = bucket or settings.S3_BUCKET_PROCESSED
        from datetime import timedelta
        url = self.client.presigned_get_object(
            bucket, path, expires=timedelta(hours=expires_hours),
        )
        return url

    def delete_file(self, path: str, bucket: str = None):
        bucket = bucket or settings.S3_BUCKET_RAW
        self.client.remove_object(bucket, path)

    def list_files(self, prefix: str, bucket: str = None) -> list[str]:
        bucket = bucket or settings.S3_BUCKET_RAW
        objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]
