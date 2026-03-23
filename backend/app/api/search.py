"""Search API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.search_service import SearchService
from app.api.posts import _post_to_response
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/")
async def search(
    q: str = Query(min_length=1, max_length=200),
    search_type: str = Query(default="all", pattern=r"^(all|users|posts|hashtags)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)

    if search_type == "users":
        users, total = await service.search_users(q, page, page_size)
        return {
            "users": [
                {"id": str(u.id), "username": u.username, "display_name": u.display_name, "avatar_url": u.avatar_url, "is_verified": u.is_verified}
                for u in users
            ],
            "total_users": total,
        }
    elif search_type == "posts":
        posts, total = await service.search_posts(q, page, page_size)
        return {
            "posts": [_post_to_response(p) for p in posts],
            "total_posts": total,
        }
    elif search_type == "hashtags":
        hashtags, total = await service.search_hashtags(q, page, page_size)
        return {
            "hashtags": [{"id": str(h.id), "name": h.name, "post_count": h.post_count} for h in hashtags],
            "total_hashtags": total,
        }
    else:
        result = await service.search_all(q, page, page_size)
        return {
            "users": [
                {"id": str(u.id), "username": u.username, "display_name": u.display_name, "avatar_url": u.avatar_url, "is_verified": u.is_verified}
                for u in result["users"]
            ],
            "posts": [_post_to_response(p) for p in result["posts"]],
            "hashtags": [{"id": str(h.id), "name": h.name, "post_count": h.post_count} for h in result["hashtags"]],
            "total_users": result["total_users"],
            "total_posts": result["total_posts"],
            "total_hashtags": result["total_hashtags"],
        }


@router.get("/suggestions")
async def get_suggestions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    users = await service.get_suggested_users(current_user["user_id"], limit=10)
    hashtags = await service.get_trending_hashtags(limit=10)
    return {
        "suggested_users": [
            {"id": str(u.id), "username": u.username, "display_name": u.display_name, "avatar_url": u.avatar_url, "is_verified": u.is_verified}
            for u in users
        ],
        "trending_hashtags": [{"id": str(h.id), "name": h.name, "post_count": h.post_count} for h in hashtags],
    }
