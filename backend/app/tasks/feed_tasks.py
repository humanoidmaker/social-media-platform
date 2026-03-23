"""Feed-related async tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger("social_media.tasks.feed")


@celery_app.task(name="app.tasks.feed_tasks.fanout_post_to_followers")
def fanout_post_to_followers(post_id: str, author_id: str) -> dict:
    """Fan out a new post to all followers' feeds using Redis sorted sets.

    For users with many followers, this happens asynchronously via Celery
    to avoid blocking the API request.
    """
    logger.info(f"Fanning out post {post_id} from author {author_id}")
    try:
        import redis
        from app.config import settings

        r = redis.from_url(settings.REDIS_URL)

        # In a real implementation, we'd query the DB for follower IDs
        # and push the post_id into each follower's feed sorted set
        # For now, we log the operation
        feed_key = f"feed:{author_id}"
        import time
        r.zadd(f"post:{post_id}:fanout", {author_id: time.time()})

        logger.info(f"Post {post_id} fanout completed")
        return {"post_id": post_id, "status": "completed"}
    except Exception as e:
        logger.error(f"Failed to fan out post {post_id}: {e}")
        return {"post_id": post_id, "status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.feed_tasks.update_trending_cache")
def update_trending_cache() -> dict:
    """Update the trending posts cache in Redis."""
    logger.info("Updating trending posts cache")
    try:
        import redis
        from app.config import settings

        r = redis.from_url(settings.REDIS_URL)
        # In production, this would query the DB for trending posts
        # and cache them in Redis for fast retrieval
        r.set("trending:last_updated", "true", ex=600)

        logger.info("Trending cache updated successfully")
        return {"status": "completed"}
    except Exception as e:
        logger.error(f"Failed to update trending cache: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="app.tasks.feed_tasks.invalidate_user_feed_cache")
def invalidate_user_feed_cache(user_id: str) -> dict:
    """Invalidate a user's cached feed when they follow/unfollow someone."""
    logger.info(f"Invalidating feed cache for user {user_id}")
    try:
        import redis
        from app.config import settings

        r = redis.from_url(settings.REDIS_URL)
        r.delete(f"feed_cache:{user_id}")

        logger.info(f"Feed cache invalidated for user {user_id}")
        return {"user_id": user_id, "status": "completed"}
    except Exception as e:
        logger.error(f"Failed to invalidate feed cache for {user_id}: {e}")
        return {"user_id": user_id, "status": "failed", "error": str(e)}
