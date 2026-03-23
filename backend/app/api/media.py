"""Media upload API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.media_service import MediaService
from app.services.post_service import PostService
from app.models.post_media import PostMedia, MediaType
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/upload/{post_id}")
async def upload_post_media(
    post_id: str,
    file: UploadFile = File(...),
    alt_text: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload media to an existing post."""
    service = PostService(db)
    post = await service.get_by_id(post_id)
    if not post or str(post.author_id) != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found or not authorized")

    data = await file.read()
    content_type = file.content_type or "application/octet-stream"

    # Determine media type
    if content_type.startswith("image/"):
        error = MediaService.validate_image(content_type, len(data))
        media_type = MediaType.IMAGE
    elif content_type.startswith("video/"):
        error = MediaService.validate_video(content_type, len(data))
        media_type = MediaType.VIDEO
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported media type")

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
    key, url = MediaService.upload_post_media(data, content_type, extension)

    # Count existing media for sort order
    existing_count = len(post.media) if post.media else 0

    post_media = PostMedia(
        post_id=uuid.UUID(post_id),
        media_type=media_type,
        url=url,
        storage_key=key,
        alt_text=alt_text,
        file_size_bytes=len(data),
        sort_order=existing_count,
    )
    db.add(post_media)
    await db.flush()

    # Trigger async media processing
    from app.tasks.media_tasks import process_image, process_video
    from app.config import settings

    if media_type == MediaType.IMAGE:
        process_image.delay(str(post_media.id), settings.MINIO_BUCKET_MEDIA, key)
    elif media_type == MediaType.VIDEO:
        process_video.delay(str(post_media.id), settings.MINIO_BUCKET_MEDIA, key)

    return {
        "id": str(post_media.id),
        "media_type": post_media.media_type.value,
        "url": url,
        "storage_key": key,
        "sort_order": post_media.sort_order,
    }


@router.delete("/{media_id}")
async def delete_post_media(
    media_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific media item from a post."""
    from sqlalchemy import select
    mid = uuid.UUID(media_id)
    result = await db.execute(select(PostMedia).where(PostMedia.id == mid))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    # Check ownership
    service = PostService(db)
    post = await service.get_by_id(str(media.post_id))
    if not post or str(post.author_id) != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    from app.config import settings
    MediaService.delete_media(settings.MINIO_BUCKET_MEDIA, media.storage_key)
    if media.thumbnail_key:
        MediaService.delete_media(settings.MINIO_BUCKET_MEDIA, media.thumbnail_key)

    await db.delete(media)
    await db.flush()
    return {"message": "Media deleted successfully"}
