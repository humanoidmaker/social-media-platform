"""Like/unlike API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.post_service import PostService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/posts/{post_id}")
async def like_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.like_post(current_user["user_id"], post_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already liked or post not found")
    return {"message": "Post liked successfully"}


@router.delete("/posts/{post_id}")
async def unlike_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.unlike_post(current_user["user_id"], post_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Like not found")
    return {"message": "Post unliked successfully"}


@router.get("/posts/{post_id}")
async def get_post_likes(
    post_id: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    users, total = await service.get_post_likes(post_id, page, page_size)
    return {
        "items": [
            {"id": str(u.id), "username": u.username, "display_name": u.display_name, "avatar_url": u.avatar_url, "is_verified": u.is_verified}
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/comments/{comment_id}")
async def like_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.like_comment(current_user["user_id"], comment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already liked or comment not found")
    return {"message": "Comment liked successfully"}


@router.delete("/comments/{comment_id}")
async def unlike_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.unlike_comment(current_user["user_id"], comment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Like not found")
    return {"message": "Comment unliked successfully"}
