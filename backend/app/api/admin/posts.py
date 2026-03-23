"""Admin post management API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.post_service import PostService
from app.middleware.auth_middleware import require_admin

router = APIRouter()


@router.get("/")
async def list_posts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    posts, total = await service.list_posts_admin(page, page_size, search)
    return {
        "items": [
            {
                "id": str(p.id),
                "author_id": str(p.author_id),
                "author_username": p.author.username if p.author else "unknown",
                "content": (p.content or "")[:200],
                "post_type": p.post_type.value if hasattr(p.post_type, "value") else p.post_type,
                "visibility": p.visibility.value if hasattr(p.visibility, "value") else p.visibility,
                "like_count": p.like_count,
                "comment_count": p.comment_count,
                "is_hidden": p.is_hidden,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in posts
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{post_id}")
async def get_post(
    post_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return {
        "id": str(post.id),
        "author_id": str(post.author_id),
        "author_username": post.author.username if post.author else "unknown",
        "content": post.content,
        "post_type": post.post_type.value if hasattr(post.post_type, "value") else post.post_type,
        "visibility": post.visibility.value if hasattr(post.visibility, "value") else post.visibility,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "repost_count": post.repost_count,
        "view_count": post.view_count,
        "is_hidden": post.is_hidden,
        "is_pinned": post.is_pinned,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    }


@router.post("/{post_id}/hide")
async def hide_post(
    post_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.hide_post(post_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return {"message": "Post hidden successfully"}


@router.post("/{post_id}/unhide")
async def unhide_post(
    post_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.unhide_post(post_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return {"message": "Post unhidden successfully"}


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.delete(post_id, current_user["user_id"], is_admin=True)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return {"message": "Post deleted successfully"}
