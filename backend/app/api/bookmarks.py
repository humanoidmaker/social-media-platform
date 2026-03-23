"""Bookmark API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.post_service import PostService
from app.middleware.auth_middleware import get_current_user
from app.api.posts import _post_to_response

router = APIRouter()


@router.post("/posts/{post_id}")
async def bookmark_post(
    post_id: str,
    collection_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.bookmark_post(current_user["user_id"], post_id, collection_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already bookmarked or post not found")
    return {"message": "Post bookmarked successfully"}


@router.delete("/posts/{post_id}")
async def unbookmark_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.unbookmark_post(current_user["user_id"], post_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return {"message": "Bookmark removed successfully"}


@router.get("/")
async def get_bookmarks(
    page: int = 1,
    page_size: int = 20,
    collection_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    posts, total = await service.get_user_bookmarks(current_user["user_id"], page, page_size, collection_id)
    return {
        "items": [_post_to_response(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
