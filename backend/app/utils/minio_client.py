"""MinIO/S3 client wrapper."""

import io
from datetime import timedelta
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import settings

_client: Optional[Minio] = None


def get_minio_client() -> Minio:
    """Get or create a MinIO client singleton."""
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


def ensure_bucket(bucket_name: str) -> None:
    """Create a bucket if it doesn't exist."""
    client = get_minio_client()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def upload_file(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload a file to MinIO. Returns the key."""
    client = get_minio_client()
    ensure_bucket(bucket)
    client.put_object(
        bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return key


def download_file(bucket: str, key: str) -> bytes:
    """Download a file from MinIO."""
    client = get_minio_client()
    response = client.get_object(bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def get_presigned_url(bucket: str, key: str, expires: timedelta = timedelta(hours=1)) -> str:
    """Get a presigned URL for file download."""
    client = get_minio_client()
    return client.presigned_get_object(bucket, key, expires=expires)


def delete_file(bucket: str, key: str) -> None:
    """Delete a file from MinIO."""
    client = get_minio_client()
    try:
        client.remove_object(bucket, key)
    except S3Error:
        pass


def file_exists(bucket: str, key: str) -> bool:
    """Check if a file exists in MinIO."""
    client = get_minio_client()
    try:
        client.stat_object(bucket, key)
        return True
    except S3Error:
        return False
