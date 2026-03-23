"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "social_media",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "expire-stories-every-5-minutes": {
        "task": "app.tasks.story_expiration_tasks.expire_stories",
        "schedule": crontab(minute="*/5"),
    },
    "daily-analytics": {
        "task": "app.tasks.analytics_tasks.aggregate_daily_stats",
        "schedule": crontab(hour=1, minute=0),
    },
    "cleanup-old-data-daily": {
        "task": "app.tasks.cleanup_tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0),
    },
    "cleanup-expired-stories-daily": {
        "task": "app.tasks.cleanup_tasks.cleanup_expired_story_media",
        "schedule": crontab(hour=3, minute=0),
    },
}

celery_app.autodiscover_tasks(["app.tasks"])
