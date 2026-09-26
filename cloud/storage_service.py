"""
Cloud object storage service.

Two interchangeable backends behind one interface:
  * LocalStorage - files under ./uploads (free, offline, for development)
  * S3Storage    - any S3-compatible bucket: AWS S3, Cloudflare R2, Supabase Storage (S3 API), MinIO

Buckets are PRIVATE. Files are only reachable through the API (after authorization checks)
or through short-lived signed URLs.
"""
from abc import ABC, abstractmethod
from pathlib import Path

from backend.config import settings


class StorageError(Exception):
    """Raised for any storage failure; the API maps it to HTTP 503."""


class BaseStorage(ABC):
    @abstractmethod
    def save(self, path: str, data: bytes, content_type: str) -> None: ...

    @abstractmethod
    def read(self, path: str) -> bytes: ...

    @abstractmethod
    def delete(self, path: str) -> None: ...

    def signed_url(self, path: str, filename: str, expires: int = 300) -> str | None:
        return None  # not supported by default


class LocalStorage(BaseStorage):
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        full = (self.root / path).resolve()
        if self.root not in full.parents:  # path-traversal guard
            raise StorageError("Invalid storage path")
        return full

    def save(self, path, data, content_type):
        try:
            full = self._resolve(path)
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(data)
        except OSError as exc:
            raise StorageError(f"Could not save file: {exc}") from exc

    def read(self, path):
        try:
            return self._resolve(path).read_bytes()
        except OSError as exc:
            raise StorageError(f"Could not read file: {exc}") from exc

    def delete(self, path):
        try:
            self._resolve(path).unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError(f"Could not delete file: {exc}") from exc


class S3Storage(BaseStorage):
    def __init__(self):
        import boto3  # imported lazily so local mode needs no cloud SDK config

        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET must be set when STORAGE_BACKEND=s3")
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            region_name=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )

    def save(self, path, data, content_type):
        try:
            extra = {} if settings.s3_endpoint_url else {"ServerSideEncryption": "AES256"}  # encryption at rest
            self.client.put_object(Bucket=self.bucket, Key=path, Body=data, ContentType=content_type, **extra)
        except Exception as exc:  # botocore raises many exception types
            raise StorageError(f"Cloud upload failed: {exc}") from exc

    def read(self, path):
        try:
            return self.client.get_object(Bucket=self.bucket, Key=path)["Body"].read()
        except Exception as exc:
            raise StorageError(f"Cloud download failed: {exc}") from exc

    def delete(self, path):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=path)
        except Exception as exc:
            raise StorageError(f"Cloud delete failed: {exc}") from exc

    def signed_url(self, path, filename, expires=300):
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket, "Key": path,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=expires,
        )


_storage: BaseStorage | None = None


def get_storage() -> BaseStorage:
    """Singleton accessor (also the seam tests use to inject a fake/failing storage)."""
    global _storage
    if _storage is None:
        _storage = S3Storage() if settings.storage_backend == "s3" else LocalStorage(settings.storage_local_dir)
    return _storage
