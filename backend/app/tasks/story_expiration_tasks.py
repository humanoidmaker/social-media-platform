"""Story expiration tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("social_media.tasks.story_expiration")


@celery_app.task(name="app.tasks.story_expiration_tasks.expire_stories")
def expire_stories() -> dict:
    """Mark expired stories as inactive."""
    logger.info("Running story expiration task")
    try:
        import asyncio
        from app.database import async_session_factory
        from app.services.story_service import StoryService

        async def _expire():
            async with async_session_factory() as session:
                service = StoryService(session)
                count = await service.expire_stories()
                await session.commit()
                return count

        count = asyncio.get_event_loop().run_until_complete(_expire())
        logger.info(f"Expired {count} stories")
        return {"expired": count, "status": "completed"}
    except Exception as e:
        logger.error(f"Story expiration failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.story_expiration_tasks.expire_single_story")
def expire_single_story(story_id: str) -> dict:
    """Expire a specific story (called by delayed task)."""
    logger.info(f"Expiring story {story_id}")
    try:
        import asyncio
        from app.database import async_session_factory
        from app.services.story_service import StoryService

        async def _expire_one():
            async with async_session_factory() as session:
                service = StoryService(session)
                story = await service.get_by_id(story_id)
                if story and story.is_active:
                    story.is_active = False
                    await session.commit()
                    return True
                return False

        expired = asyncio.get_event_loop().run_until_complete(_expire_one())
        return {"story_id": story_id, "expired": expired}
    except Exception as e:
        logger.error(f"Failed to expire story {story_id}: {e}")
        return {"story_id": story_id, "status": "failed", "error": str(e)}
