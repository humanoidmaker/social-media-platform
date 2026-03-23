"""Users API routes - profiles, avatar/banner uploads."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UpdateProfileRequest
from app.services.user_service import UserService
from app.services.media_service import MediaService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


def _user_to_public(user) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "display_name": user.display_name,
        "bio": user.bio,
        "website": user.website,
        "location": user.location,
        "avatar_url": user.avatar_url,
        "banner_url": user.banner_url,
        "is_verified": user.is_verified,
        "is_private": user.is_private,
        "follower_count": user.follower_count,
        "following_count": user.following_count,
        "post_count": user.post_count,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/{username}")
async def get_user_profile(username: str, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user = await service.get_by_username(username)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_to_public(user)


@router.patch("/me/profile")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    update_data = data.model_dump(exclude_none=True)
    user = await service.update_profile(current_user["user_id"], **update_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_to_public(user)


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    error = MediaService.validate_image(file.content_type, len(data))
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    key, url = MediaService.upload_avatar(data, file.content_type, extension)

    service = UserService(db)
    user = await service.get_by_id(current_user["user_id"])
    if user and user.avatar_key:
        from app.config import settings
        MediaService.delete_media(settings.MINIO_BUCKET_AVATARS, user.avatar_key)

    await service.update_profile(current_user["user_id"], avatar_url=url, avatar_key=key)
    return {"avatar_url": url}


@router.post("/me/banner")
async def upload_banner(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    error = MediaService.validate_image(file.content_type, len(data))
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    key, url = MediaService.upload_banner(data, file.content_type, extension)

    service = UserService(db)
    user = await service.get_by_id(current_user["user_id"])
    if user and user.banner_key:
        from app.config import settings
        MediaService.delete_media(settings.MINIO_BUCKET_AVATARS, user.banner_key)

    await service.update_profile(current_user["user_id"], banner_url=url, banner_key=key)
    return {"banner_url": url}


@router.get("/{username}/followers")
async def get_followers(
    username: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    followers, total = await service.get_followers(str(user.id), page, page_size)
    return {
        "items": [{"id": str(u.id), "username": u.username, "display_name": u.display_name, "avatar_url": u.avatar_url, "is_verified": u.is_verified} for u in followers],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{username}/following")
async def get_following(
    username: str,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    user = await service.get_by_username(username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    following, total = await service.get_following(str(user.id), page, page_size)
    return {
        "items": [{"id": str(u.id), "username": u.username, "display_name": u.display_name, "avatar_url": u.avatar_url, "is_verified": u.is_verified} for u in following],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
