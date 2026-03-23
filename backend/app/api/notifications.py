"""Notification API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.notification import MarkReadRequest
from app.services.notification_service import NotificationService
from app.services.user_service import UserService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.get("/")
async def get_notifications(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    user_service = UserService(db)
    notifications, total = await service.get_user_notifications(current_user["user_id"], page, page_size)
    unread = await service.get_unread_count(current_user["user_id"])

    items = []
    for n in notifications:
        actor = None
        if n.actor_id:
            actor_user = await user_service.get_by_id(str(n.actor_id))
            if actor_user:
                actor = {
                    "id": str(actor_user.id),
                    "username": actor_user.username,
                    "display_name": actor_user.display_name,
                    "avatar_url": actor_user.avatar_url,
                    "is_verified": actor_user.is_verified,
                }
        items.append({
            "id": str(n.id),
            "notification_type": n.notification_type.value,
            "title": n.title,
            "body": n.body,
            "actor": actor,
            "target_type": n.target_type,
            "target_id": str(n.target_id) if n.target_id else None,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })

    return {
        "items": items,
        "total": total,
        "unread_count": unread,
        "page": page,
        "page_size": page_size,
        "has_next": page * page_size < total,
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    count = await service.get_unread_count(current_user["user_id"])
    return {"unread_count": count}


@router.post("/mark-read")
async def mark_as_read(
    data: MarkReadRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    if data.notification_ids:
        count = await service.mark_as_read(data.notification_ids, current_user["user_id"])
    else:
        count = await service.mark_all_as_read(current_user["user_id"])
    return {"marked_read": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    success = await service.delete_notification(notification_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"message": "Notification deleted"}
