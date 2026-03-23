"""Comment API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.comment import CreateCommentRequest, UpdateCommentRequest
from app.services.post_service import PostService
from app.services.user_service import UserService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


def _comment_to_response(comment) -> dict:
    author = comment.author if comment.author else None
    return {
        "id": str(comment.id),
        "post_id": str(comment.post_id),
        "author": {
            "id": str(author.id),
            "username": author.username,
            "display_name": author.display_name,
            "avatar_url": author.avatar_url,
            "is_verified": author.is_verified,
        } if author else None,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "content": comment.content,
        "like_count": comment.like_count,
        "reply_count": comment.reply_count,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
    }


@router.get("/posts/{post_id}")
async def get_post_comments(
    post_id: str,
    page: int = 1,
    page_size: int = 20,
    parent_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    comments, total = await service.get_post_comments(post_id, page, page_size, parent_id)
    return {
        "items": [_comment_to_response(c) for c in comments],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/posts/{post_id}", status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: str,
    data: CreateCommentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.get_by_id(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.is_comments_disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Comments are disabled on this post")

    comment = await service.add_comment(post_id, current_user["user_id"], data.content, data.parent_id)
    return _comment_to_response(comment)


@router.patch("/{comment_id}")
async def update_comment(
    comment_id: str,
    data: UpdateCommentRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    comment = await service.update_comment(comment_id, current_user["user_id"], data.content)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or not authorized")
    return _comment_to_response(comment)


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    is_admin = current_user.get("role") in ("superadmin", "admin")
    success = await service.delete_comment(comment_id, current_user["user_id"], is_admin=is_admin)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found or not authorized")
    return {"message": "Comment deleted successfully"}
