"""Media service for handling file uploads."""

import uuid
from datetime import timedelta
from typing import Optional

from app.config import settings
from app.utils.minio_client import (
    upload_file,
    delete_file,
    get_presigned_url,
    ensure_bucket,
)


class MediaService:
    @staticmethod
    def validate_image(content_type: str, size_bytes: int) -> Optional[str]:
        """Validate an image file. Returns error message or None if valid."""
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            return f"Invalid image type: {content_type}. Allowed: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            return f"Image too large. Maximum size: {settings.MAX_IMAGE_SIZE_MB}MB"
        return None

    @staticmethod
    def validate_video(content_type: str, size_bytes: int) -> Optional[str]:
        """Validate a video file. Returns error message or None if valid."""
        if content_type not in settings.ALLOWED_VIDEO_TYPES:
            return f"Invalid video type: {content_type}. Allowed: {', '.join(settings.ALLOWED_VIDEO_TYPES)}"
        max_bytes = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            return f"Video too large. Maximum size: {settings.MAX_VIDEO_SIZE_MB}MB"
        return None

    @staticmethod
    def upload_post_media(data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        """Upload a post media file. Returns (key, url)."""
        key = f"posts/{uuid.uuid4()}.{extension}"
        upload_file(settings.MINIO_BUCKET_MEDIA, key, data, content_type)
        url = get_presigned_url(settings.MINIO_BUCKET_MEDIA, key, timedelta(days=7))
        return key, url

    @staticmethod
    def upload_avatar(data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        """Upload an avatar image. Returns (key, url)."""
        key = f"avatars/{uuid.uuid4()}.{extension}"
        upload_file(settings.MINIO_BUCKET_AVATARS, key, data, content_type)
        url = get_presigned_url(settings.MINIO_BUCKET_AVATARS, key, timedelta(days=7))
        return key, url

    @staticmethod
    def upload_banner(data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        """Upload a banner image. Returns (key, url)."""
        key = f"banners/{uuid.uuid4()}.{extension}"
        upload_file(settings.MINIO_BUCKET_AVATARS, key, data, content_type)
        url = get_presigned_url(settings.MINIO_BUCKET_AVATARS, key, timedelta(days=7))
        return key, url

    @staticmethod
    def upload_story_media(data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        """Upload story media. Returns (key, url)."""
        key = f"stories/{uuid.uuid4()}.{extension}"
        upload_file(settings.MINIO_BUCKET_STORIES, key, data, content_type)
        url = get_presigned_url(settings.MINIO_BUCKET_STORIES, key, timedelta(days=7))
        return key, url

    @staticmethod
    def upload_message_media(data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        """Upload message media. Returns (key, url)."""
        key = f"messages/{uuid.uuid4()}.{extension}"
        upload_file(settings.MINIO_BUCKET_MEDIA, key, data, content_type)
        url = get_presigned_url(settings.MINIO_BUCKET_MEDIA, key, timedelta(days=7))
        return key, url

    @staticmethod
    def delete_media(bucket: str, key: str) -> None:
        """Delete a media file from storage."""
        delete_file(bucket, key)

    @staticmethod
    def get_url(bucket: str, key: str) -> str:
        """Get a presigned URL for a media file."""
        return get_presigned_url(bucket, key, timedelta(days=7))

    @staticmethod
    def init_buckets() -> None:
        """Ensure all required storage buckets exist."""
        ensure_bucket(settings.MINIO_BUCKET_MEDIA)
        ensure_bucket(settings.MINIO_BUCKET_AVATARS)
        ensure_bucket(settings.MINIO_BUCKET_STORIES)
