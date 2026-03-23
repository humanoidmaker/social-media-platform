"""Feed API routes - home feed and explore."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.feed_service import FeedService
from app.api.posts import _post_to_response
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/home")
async def get_home_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the home feed: posts from followed users and self."""
    service = FeedService(db)
    posts, total = await service.get_home_feed(current_user["user_id"], page, page_size)
    return {
        "items": [_post_to_response(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/explore")
async def get_explore_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the explore feed: trending public posts."""
    service = FeedService(db)
    posts, total = await service.get_explore_feed(current_user["user_id"], page, page_size)
    return {
        "items": [_post_to_response(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
