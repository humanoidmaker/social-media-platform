"""Stories API routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.story import CreateStoryRequest, CreateHighlightRequest, UpdateHighlightRequest
from app.services.story_service import StoryService
from app.services.user_service import UserService
from app.services.media_service import MediaService
from app.middleware.auth_middleware import get_current_user
from app.models.post_media import MediaType

router = APIRouter()


def _story_to_response(story) -> dict:
    author = story.author if story.author else None
    return {
        "id": str(story.id),
        "author": {
            "id": str(author.id),
            "username": author.username,
            "display_name": author.display_name,
            "avatar_url": author.avatar_url,
            "is_verified": author.is_verified,
        } if author else None,
        "media_type": story.media_type.value if hasattr(story.media_type, "value") else story.media_type,
        "media_url": story.media_url,
        "thumbnail_url": story.thumbnail_url,
        "caption": story.caption,
        "duration_seconds": story.duration_seconds,
        "view_count": story.view_count,
        "is_close_friends": story.is_close_friends,
        "expires_at": story.expires_at.isoformat() if story.expires_at else None,
        "created_at": story.created_at.isoformat() if story.created_at else None,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_story(
    file: UploadFile = File(...),
    caption: str = Form(None),
    duration_seconds: int = Form(5),
    is_close_friends: bool = Form(False),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"

    if content_type.startswith("image/"):
        error = MediaService.validate_image(content_type, len(data))
        media_type = "image"
    elif content_type.startswith("video/"):
        error = MediaService.validate_video(content_type, len(data))
        media_type = "video"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported media type")

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
    key, url = MediaService.upload_story_media(data, content_type, extension)

    service = StoryService(db)
    story = await service.create(
        author_id=current_user["user_id"],
        media_type=media_type,
        media_url=url,
        media_key=key,
        caption=caption,
        duration_seconds=duration_seconds,
        is_close_friends=is_close_friends,
    )
    story = await service.get_by_id(str(story.id))
    return _story_to_response(story)


@router.get("/feed")
async def get_story_feed(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StoryService(db)
    user_service = UserService(db)
    grouped = await service.get_feed_stories(current_user["user_id"])

    result = []
    for author_id, stories in grouped.items():
        author = await user_service.get_by_id(author_id)
        if author:
            result.append({
                "user": {
                    "id": str(author.id),
                    "username": author.username,
                    "display_name": author.display_name,
                    "avatar_url": author.avatar_url,
                    "is_verified": author.is_verified,
                },
                "stories": [_story_to_response(s) for s in stories],
                "has_unseen": True,
            })
    return result


@router.get("/user/{username}")
async def get_user_stories(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    service = StoryService(db)
    stories = await service.get_user_stories(str(user.id))
    return [_story_to_response(s) for s in stories]


@router.get("/{story_id}")
async def get_story(story_id: str, db: AsyncSession = Depends(get_db)):
    service = StoryService(db)
    story = await service.get_by_id(story_id)
    if not story or not story.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    return _story_to_response(story)


@router.post("/{story_id}/view")
async def view_story(
    story_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StoryService(db)
    await service.view_story(story_id, current_user["user_id"])
    return {"message": "Story viewed"}


@router.get("/{story_id}/viewers")
async def get_story_viewers(
    story_id: str,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StoryService(db)
    story = await service.get_by_id(story_id)
    if not story or str(story.author_id) != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    views, total = await service.get_story_viewers(story_id, page, page_size)
    user_service = UserService(db)
    items = []
    for view in views:
        viewer = await user_service.get_by_id(str(view.viewer_id))
        if viewer:
            items.append({
                "viewer": {
                    "id": str(viewer.id),
                    "username": viewer.username,
                    "display_name": viewer.display_name,
                    "avatar_url": viewer.avatar_url,
                    "is_verified": viewer.is_verified,
                },
                "viewed_at": view.viewed_at.isoformat() if view.viewed_at else None,
            })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StoryService(db)
    success = await service.delete(story_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found or not authorized")
    return {"message": "Story deleted successfully"}


# Highlights
@router.post("/highlights", status_code=status.HTTP_201_CREATED)
async def create_highlight(
    data: CreateHighlightRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StoryService(db)
    highlight = await service.create_highlight(current_user["user_id"], data.title, data.story_ids)
    return {
        "id": str(highlight.id),
        "title": highlight.title,
        "story_ids": [str(sid) for sid in (highlight.story_ids or [])],
        "created_at": highlight.created_at.isoformat() if highlight.created_at else None,
    }


@router.get("/highlights/{username}")
async def get_user_highlights(username: str, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    service = StoryService(db)
    highlights = await service.get_user_highlights(str(user.id))
    return [
        {
            "id": str(h.id),
            "title": h.title,
            "cover_url": h.cover_url,
            "story_ids": [str(sid) for sid in (h.story_ids or [])],
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in highlights
    ]


@router.patch("/highlights/{highlight_id}")
async def update_highlight(
    highlight_id: str,
    data: UpdateHighlightRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StoryService(db)
    update_data = data.model_dump(exclude_none=True)
    highlight = await service.update_highlight(highlight_id, current_user["user_id"], **update_data)
    if not highlight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight not found or not authorized")
    return {
        "id": str(highlight.id),
        "title": highlight.title,
        "story_ids": [str(sid) for sid in (highlight.story_ids or [])],
    }


@router.delete("/highlights/{highlight_id}")
async def delete_highlight(
    highlight_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = StoryService(db)
    success = await service.delete_highlight(highlight_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Highlight not found or not authorized")
    return {"message": "Highlight deleted successfully"}
