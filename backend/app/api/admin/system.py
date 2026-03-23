"""Admin system health API routes."""

import time
import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.middleware.auth_middleware import require_admin

router = APIRouter()
logger = logging.getLogger("social_media.admin.system")

_start_time = time.time()


@router.get("/health")
async def system_health(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    health = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "minio": "unknown",
        "celery_workers": 0,
        "uptime_seconds": round(time.time() - _start_time, 2),
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
        health["redis"] = "connected"
    except Exception:
        health["redis"] = "disconnected"
        health["status"] = "degraded"

    # Check MinIO
    try:
        from app.utils.minio_client import get_minio_client
        client = get_minio_client()
        client.list_buckets()
        health["minio"] = "connected"
    except Exception:
        health["minio"] = "disconnected"
        health["status"] = "degraded"

    # Check Celery workers
    try:
        from app.tasks.celery_app import celery_app
        inspector = celery_app.control.inspect(timeout=2)
        active = inspector.active()
        if active:
            health["celery_workers"] = len(active)
    except Exception:
        pass

    return health


@router.get("/info")
async def system_info(current_user: dict = Depends(require_admin)):
    import sys
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "python_version": sys.version,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(time.time() - _start_time, 2),
    }


@router.post("/clear-cache")
async def clear_cache(current_user: dict = Depends(require_admin)):
    """Clear all Redis caches."""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.flushdb()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        return {"message": f"Failed to clear cache: {str(e)}"}
