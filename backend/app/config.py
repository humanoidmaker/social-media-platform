"""Application configuration using pydantic-settings."""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Social Media Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://socialmedia:socialmedia@localhost:5432/socialmedia"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "super-secret-social_media-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # MinIO / S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_MEDIA: str = "social_media-media"
    MINIO_BUCKET_AVATARS: str = "social_media-avatars"
    MINIO_BUCKET_STORIES: str = "social_media-stories"

    # SMTP / Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    SMTP_FROM_EMAIL: str = "noreply@social_media.io"
    SMTP_FROM_NAME: str = "Social Media Platform"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Feed
    FANOUT_FOLLOWER_THRESHOLD: int = 10000

    # Stories
    STORY_EXPIRATION_HOURS: int = 24

    # Media
    MAX_IMAGE_SIZE_MB: int = 10
    MAX_VIDEO_SIZE_MB: int = 100
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/webm", "video/quicktime"]

    # Platform
    MAX_POST_LENGTH: int = 2200
    MAX_COMMENT_LENGTH: int = 1000
    MAX_BIO_LENGTH: int = 500
    MAX_HASHTAGS_PER_POST: int = 30
    MAX_MEDIA_PER_POST: int = 10
    MAX_POLL_OPTIONS: int = 4

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
