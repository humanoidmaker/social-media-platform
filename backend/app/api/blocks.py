"""Block/unblock API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.user_service import UserService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/{user_id}")
async def block_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    block = await service.block_user(current_user["user_id"], user_id)
    if not block:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block this user")
    return {"message": "User blocked successfully"}


@router.delete("/{user_id}")
async def unblock_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    success = await service.unblock_user(current_user["user_id"], user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
    return {"message": "User unblocked successfully"}


@router.get("/")
async def get_blocked_users(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    users, total = await service.get_blocked_users(current_user["user_id"], page, page_size)
    return {
        "items": [
            {
                "id": str(u.id),
                "username": u.username,
                "display_name": u.display_name,
                "avatar_url": u.avatar_url,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
