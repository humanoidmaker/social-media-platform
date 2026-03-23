"""Posts API routes - CRUD, repost."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.post import CreatePostRequest, UpdatePostRequest, RepostRequest
from app.services.post_service import PostService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


def _post_to_response(post) -> dict:
    author = post.author if post.author else None
    media_list = []
    if post.media:
        for m in post.media:
            media_list.append({
                "id": str(m.id),
                "media_type": m.media_type.value if hasattr(m.media_type, "value") else m.media_type,
                "url": m.url,
                "thumbnail_url": m.thumbnail_url,
                "width": m.width,
                "height": m.height,
                "duration_seconds": m.duration_seconds,
                "alt_text": m.alt_text,
                "sort_order": m.sort_order,
            })

    poll_data = None
    if post.poll:
        poll_data = {
            "id": str(post.poll.id),
            "total_votes": post.poll.total_votes,
            "expires_at": post.poll.expires_at.isoformat() if post.poll.expires_at else None,
            "options": [
                {"id": str(o.id), "text": o.text, "vote_count": o.vote_count, "sort_order": o.sort_order}
                for o in (post.poll.options or [])
            ],
        }

    original = None
    if post.original_post:
        original = {
            "id": str(post.original_post.id),
            "content": post.original_post.content,
            "post_type": post.original_post.post_type.value if hasattr(post.original_post.post_type, "value") else post.original_post.post_type,
            "author": {
                "id": str(post.original_post.author.id),
                "username": post.original_post.author.username,
                "display_name": post.original_post.author.display_name,
                "avatar_url": post.original_post.author.avatar_url,
                "is_verified": post.original_post.author.is_verified,
            } if post.original_post.author else None,
        }

    return {
        "id": str(post.id),
        "author": {
            "id": str(author.id),
            "username": author.username,
            "display_name": author.display_name,
            "avatar_url": author.avatar_url,
            "is_verified": author.is_verified,
        } if author else None,
        "content": post.content,
        "post_type": post.post_type.value if hasattr(post.post_type, "value") else post.post_type,
        "visibility": post.visibility.value if hasattr(post.visibility, "value") else post.visibility,
        "location": post.location,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "repost_count": post.repost_count,
        "bookmark_count": post.bookmark_count,
        "view_count": post.view_count,
        "is_pinned": post.is_pinned,
        "is_comments_disabled": post.is_comments_disabled,
        "media": media_list,
        "poll": poll_data,
        "original_post": original,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_post(
    data: CreatePostRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.create(
        author_id=current_user["user_id"],
        content=data.content,
        post_type=data.post_type,
        visibility=data.visibility,
        location=data.location,
        is_comments_disabled=data.is_comments_disabled,
        poll_options=data.poll_options,
        poll_expires_hours=data.poll_expires_hours,
    )
    # Refresh to get relationships
    post = await service.get_by_id(str(post.id))
    return _post_to_response(post)


@router.get("/{post_id}")
async def get_post(post_id: str, db: AsyncSession = Depends(get_db)):
    service = PostService(db)
    post = await service.get_by_id(post_id)
    if not post or post.is_hidden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return _post_to_response(post)


@router.patch("/{post_id}")
async def update_post(
    post_id: str,
    data: UpdatePostRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    update_data = data.model_dump(exclude_none=True)
    post = await service.update(post_id, current_user["user_id"], **update_data)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found or not authorized")
    return _post_to_response(post)


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    is_admin = current_user.get("role") in ("superadmin", "admin")
    success = await service.delete(post_id, current_user["user_id"], is_admin=is_admin)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found or not authorized")
    return {"message": "Post deleted successfully"}


@router.post("/{post_id}/repost")
async def repost(
    post_id: str,
    data: RepostRequest = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    quote = data.quote_content if data else None
    repost = await service.repost(current_user["user_id"], post_id, quote)
    if not repost:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original post not found")
    repost = await service.get_by_id(str(repost.id))
    return _post_to_response(repost)


@router.post("/{post_id}/pin")
async def pin_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.pin_post(post_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot pin this post")
    return {"message": "Post pinned successfully"}


@router.delete("/{post_id}/pin")
async def unpin_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.unpin_post(post_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot unpin this post")
    return {"message": "Post unpinned successfully"}


@router.get("/user/{username}")
async def get_user_posts(
    username: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    from app.services.user_service import UserService
    user_service = UserService(db)
    user = await user_service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    service = PostService(db)
    posts, total = await service.get_user_posts(str(user.id), page, page_size)
    return {
        "items": [_post_to_response(p) for p in posts],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
