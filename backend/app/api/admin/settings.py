"""Admin settings API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.schemas.admin import UpdateAdminSettingsRequest
from app.middleware.auth_middleware import require_admin

router = APIRouter()

# Runtime-configurable settings stored in memory
# In production, these would be stored in Redis or the database
_runtime_settings = {
    "max_post_length": settings.MAX_POST_LENGTH,
    "max_comment_length": settings.MAX_COMMENT_LENGTH,
    "max_media_per_post": settings.MAX_MEDIA_PER_POST,
    "story_expiration_hours": settings.STORY_EXPIRATION_HOURS,
    "rate_limit_requests": settings.RATE_LIMIT_REQUESTS,
    "maintenance_mode": False,
}


@router.get("/")
async def get_settings(current_user: dict = Depends(require_admin)):
    return _runtime_settings


@router.patch("/")
async def update_settings(
    data: UpdateAdminSettingsRequest,
    current_user: dict = Depends(require_admin),
):
    update_data = data.model_dump(exclude_none=True)
    _runtime_settings.update(update_data)
    return {"message": "Settings updated successfully", "settings": _runtime_settings}


@router.get("/maintenance")
async def get_maintenance_status(current_user: dict = Depends(require_admin)):
    return {"maintenance_mode": _runtime_settings["maintenance_mode"]}


@router.post("/maintenance/enable")
async def enable_maintenance(current_user: dict = Depends(require_admin)):
    _runtime_settings["maintenance_mode"] = True
    return {"message": "Maintenance mode enabled"}


@router.post("/maintenance/disable")
async def disable_maintenance(current_user: dict = Depends(require_admin)):
    _runtime_settings["maintenance_mode"] = False
    return {"message": "Maintenance mode disabled"}
