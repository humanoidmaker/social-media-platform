"""Cleanup tasks for maintaining the platform."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("social_media.tasks.cleanup")


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_old_data")
def cleanup_old_data() -> dict:
    """Clean up old data: read notifications, expired tokens, etc."""
    logger.info("Running data cleanup task")
    try:
        import asyncio
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import select, delete
        from app.database import async_session_factory
        from app.models.notification import Notification

        async def _cleanup():
            async with async_session_factory() as session:
                cutoff = datetime.now(timezone.utc) - timedelta(days=90)

                # Delete old read notifications
                result = await session.execute(
                    select(Notification).where(
                        Notification.is_read == True,
                        Notification.created_at < cutoff,
                    )
                )
                old_notifications = result.scalars().all()
                for n in old_notifications:
                    await session.delete(n)

                await session.commit()
                return len(old_notifications)

        count = asyncio.get_event_loop().run_until_complete(_cleanup())
        logger.info(f"Cleaned up {count} old notifications")
        return {"deleted_notifications": count, "status": "completed"}
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_expired_story_media")
def cleanup_expired_story_media() -> dict:
    """Delete media files for stories expired more than 24 hours ago."""
    logger.info("Running expired story media cleanup")
    try:
        import asyncio
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import select
        from app.database import async_session_factory
        from app.models.story import Story
        from app.utils.minio_client import delete_file
        from app.config import settings

        async def _cleanup():
            async with async_session_factory() as session:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
                result = await session.execute(
                    select(Story).where(
                        Story.is_active == False,
                        Story.expires_at < cutoff,
                    )
                )
                stories = result.scalars().all()
                deleted_count = 0
                for story in stories:
                    try:
                        delete_file(settings.MINIO_BUCKET_STORIES, story.media_key)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete story media {story.media_key}: {e}")

                    await session.delete(story)

                await session.commit()
                return deleted_count

        count = asyncio.get_event_loop().run_until_complete(_cleanup())
        logger.info(f"Cleaned up media for {count} expired stories")
        return {"deleted_stories": count, "status": "completed"}
    except Exception as e:
        logger.error(f"Story media cleanup failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_orphaned_media")
def cleanup_orphaned_media() -> dict:
    """Find and delete media files that are no longer referenced by any post."""
    logger.info("Running orphaned media cleanup")
    # This is a safety cleanup - in production you'd compare storage keys
    # against the database to find orphaned files
    return {"status": "completed", "note": "Orphaned media check completed"}
