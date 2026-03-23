"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import (
    auth,
    users,
    follows,
    blocks,
    posts,
    media,
    likes,
    comments,
    bookmarks,
    stories,
    polls,
    messages,
    hashtags,
    search,
    notifications,
    reports,
    feed,
    collections,
    websocket,
)
from app.api.admin import (
    dashboard as admin_dashboard,
    users as admin_users,
    posts as admin_posts,
    reports as admin_reports,
    hashtags as admin_hashtags,
    analytics as admin_analytics,
    system as admin_system,
    settings as admin_settings,
)
from app.middleware.request_logger import RequestLoggerMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "development":
        await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Social Media Platform Social Media Platform API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(RateLimiterMiddleware)

# Public API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(follows.router, prefix="/api/follows", tags=["Follows"])
app.include_router(blocks.router, prefix="/api/blocks", tags=["Blocks"])
app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])
app.include_router(media.router, prefix="/api/media", tags=["Media"])
app.include_router(likes.router, prefix="/api/likes", tags=["Likes"])
app.include_router(comments.router, prefix="/api/comments", tags=["Comments"])
app.include_router(bookmarks.router, prefix="/api/bookmarks", tags=["Bookmarks"])
app.include_router(stories.router, prefix="/api/stories", tags=["Stories"])
app.include_router(polls.router, prefix="/api/polls", tags=["Polls"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(hashtags.router, prefix="/api/hashtags", tags=["Hashtags"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(feed.router, prefix="/api/feed", tags=["Feed"])
app.include_router(collections.router, prefix="/api/collections", tags=["Collections"])

# Admin routes
app.include_router(admin_dashboard.router, prefix="/api/admin/dashboard", tags=["Admin Dashboard"])
app.include_router(admin_users.router, prefix="/api/admin/users", tags=["Admin Users"])
app.include_router(admin_posts.router, prefix="/api/admin/posts", tags=["Admin Posts"])
app.include_router(admin_reports.router, prefix="/api/admin/reports", tags=["Admin Reports"])
app.include_router(admin_hashtags.router, prefix="/api/admin/hashtags", tags=["Admin Hashtags"])
app.include_router(admin_analytics.router, prefix="/api/admin/analytics", tags=["Admin Analytics"])
app.include_router(admin_system.router, prefix="/api/admin/system", tags=["Admin System"])
app.include_router(admin_settings.router, prefix="/api/admin/settings", tags=["Admin Settings"])

# WebSocket
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}
