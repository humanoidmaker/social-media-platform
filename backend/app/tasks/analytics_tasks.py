"""Analytics aggregation tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("social_media.tasks.analytics")


@celery_app.task(name="app.tasks.analytics_tasks.aggregate_daily_stats")
def aggregate_daily_stats() -> dict:
    """Aggregate and store daily platform statistics."""
    logger.info("Running daily analytics aggregation")
    try:
        import asyncio
        from app.database import async_session_factory
        from app.services.analytics_service import AnalyticsService

        async def _aggregate():
            async with async_session_factory() as session:
                service = AnalyticsService(session)
                await service.save_daily_stats()
                await session.commit()

        asyncio.get_event_loop().run_until_complete(_aggregate())
        logger.info("Daily analytics aggregation completed")
        return {"status": "completed"}
    except Exception as e:
        logger.error(f"Daily analytics aggregation failed: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.analytics_tasks.track_post_view")
def track_post_view(post_id: str, viewer_id: str = None) -> dict:
    """Track a post view asynchronously."""
    try:
        import asyncio
        from app.database import async_session_factory
        from app.services.post_service import PostService

        async def _track():
            async with async_session_factory() as session:
                service = PostService(session)
                await service.increment_view(post_id)
                await session.commit()

        asyncio.get_event_loop().run_until_complete(_track())
        return {"post_id": post_id, "status": "tracked"}
    except Exception as e:
        logger.error(f"Failed to track view for post {post_id}: {e}")
        return {"post_id": post_id, "status": "failed"}


@celery_app.task(name="app.tasks.analytics_tasks.update_hashtag_trending_scores")
def update_hashtag_trending_scores() -> dict:
    """Recalculate trending scores for hashtags."""
    logger.info("Updating hashtag trending scores")
    try:
        import redis
        import asyncio
        from app.config import settings
        from app.database import async_session_factory
        from app.services.search_service import SearchService

        async def _update():
            async with async_session_factory() as session:
                service = SearchService(session)
                trending = await service.get_trending_hashtags(limit=50)
                r = redis.from_url(settings.REDIS_URL)
                pipe = r.pipeline()
                pipe.delete("trending:hashtags")
                for i, h in enumerate(trending):
                    pipe.zadd("trending:hashtags", {h.name: h.post_count})
                pipe.expire("trending:hashtags", 3600)
                pipe.execute()
                return len(trending)

        count = asyncio.get_event_loop().run_until_complete(_update())
        logger.info(f"Updated trending scores for {count} hashtags")
        return {"status": "completed", "count": count}
    except Exception as e:
        logger.error(f"Failed to update hashtag trending scores: {e}")
        return {"status": "failed", "error": str(e)}
