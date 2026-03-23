"""Hashtag API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.search_service import SearchService
from app.services.feed_service import FeedService
from app.api.posts import _post_to_response

router = APIRouter()


@router.get("/trending")
async def get_trending_hashtags(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    hashtags = await service.get_trending_hashtags(limit)
    return [
        {"id": str(h.id), "name": h.name, "post_count": h.post_count}
        for h in hashtags
    ]


@router.get("/{hashtag_name}")
async def get_hashtag_posts(
    hashtag_name: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    feed_service = FeedService(db)
    posts, total = await feed_service.get_hashtag_feed(hashtag_name, page, page_size)
    return {
        "hashtag": hashtag_name,
        "items": [_post_to_response(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{hashtag_name}/info")
async def get_hashtag_info(
    hashtag_name: str,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.hashtag import Hashtag

    result = await db.execute(select(Hashtag).where(Hashtag.name == hashtag_name.lower()))
    hashtag = result.scalar_one_or_none()
    if not hashtag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hashtag not found")
    return {"id": str(hashtag.id), "name": hashtag.name, "post_count": hashtag.post_count}
