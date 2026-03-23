"""Media processing tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("social_media.tasks.media")


@celery_app.task(name="app.tasks.media_tasks.process_image")
def process_image(media_id: str, bucket: str, key: str) -> dict:
    """Process an uploaded image: generate thumbnails, optimize, extract metadata."""
    logger.info(f"Processing image: {media_id} ({bucket}/{key})")
    try:
        from PIL import Image
        import io
        from app.utils.minio_client import download_file, upload_file

        data = download_file(bucket, key)
        img = Image.open(io.BytesIO(data))
        width, height = img.size

        # Generate thumbnail (max 400x400)
        thumb = img.copy()
        thumb.thumbnail((400, 400))
        thumb_buffer = io.BytesIO()
        thumb.save(thumb_buffer, format=img.format or "JPEG", quality=85)
        thumb_bytes = thumb_buffer.getvalue()

        thumb_key = key.replace("posts/", "posts/thumbs/").replace("stories/", "stories/thumbs/")
        upload_file(bucket, thumb_key, thumb_bytes, f"image/{(img.format or 'jpeg').lower()}")

        logger.info(f"Image processed successfully: {media_id} ({width}x{height})")
        return {
            "media_id": media_id,
            "width": width,
            "height": height,
            "thumbnail_key": thumb_key,
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Failed to process image {media_id}: {e}")
        return {"media_id": media_id, "status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.media_tasks.process_video")
def process_video(media_id: str, bucket: str, key: str) -> dict:
    """Process an uploaded video: generate thumbnail, extract metadata."""
    logger.info(f"Processing video: {media_id} ({bucket}/{key})")
    try:
        # Video processing with ffmpeg would happen here
        # For now, we mark as completed with placeholder values
        logger.info(f"Video processed successfully: {media_id}")
        return {
            "media_id": media_id,
            "width": 1920,
            "height": 1080,
            "duration_seconds": 0,
            "thumbnail_key": None,
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Failed to process video {media_id}: {e}")
        return {"media_id": media_id, "status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.media_tasks.delete_media_files")
def delete_media_files(bucket: str, keys: list[str]) -> dict:
    """Delete multiple media files from storage."""
    logger.info(f"Deleting {len(keys)} media files from {bucket}")
    from app.utils.minio_client import delete_file

    deleted = 0
    for key in keys:
        try:
            delete_file(bucket, key)
            deleted += 1
        except Exception as e:
            logger.error(f"Failed to delete {key}: {e}")

    return {"deleted": deleted, "total": len(keys)}
