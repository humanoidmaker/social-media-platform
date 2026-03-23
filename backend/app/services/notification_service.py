"""Notification service."""

import uuid
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        recipient_id: str,
        notification_type: str,
        title: str,
        body: Optional[str] = None,
        actor_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> Notification:
        rid = uuid.UUID(recipient_id)
        aid = uuid.UUID(actor_id) if actor_id else None
        tid = uuid.UUID(target_id) if target_id else None

        # Don't notify yourself
        if actor_id and actor_id == recipient_id:
            return None

        notification = Notification(
            recipient_id=rid,
            actor_id=aid,
            notification_type=NotificationType(notification_type),
            title=title,
            body=body,
            target_type=target_type,
            target_id=tid,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_user_notifications(self, user_id: str, page: int = 1, page_size: int = 20):
        uid = uuid.UUID(user_id)
        query = (
            select(Notification)
            .where(Notification.recipient_id == uid)
            .order_by(Notification.created_at.desc())
        )
        count_query = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_id == uid)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_unread_count(self, user_id: str) -> int:
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.recipient_id == uid, Notification.is_read == False)
        )
        return result.scalar() or 0

    async def mark_as_read(self, notification_ids: list[str], user_id: str) -> int:
        uid = uuid.UUID(user_id)
        nids = [uuid.UUID(nid) for nid in notification_ids]
        result = await self.db.execute(
            select(Notification).where(
                Notification.id.in_(nids),
                Notification.recipient_id == uid,
                Notification.is_read == False,
            )
        )
        notifications = result.scalars().all()
        for n in notifications:
            n.is_read = True
        await self.db.flush()
        return len(notifications)

    async def mark_all_as_read(self, user_id: str) -> int:
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(Notification).where(
                Notification.recipient_id == uid,
                Notification.is_read == False,
            )
        )
        notifications = result.scalars().all()
        for n in notifications:
            n.is_read = True
        await self.db.flush()
        return len(notifications)

    async def delete_notification(self, notification_id: str, user_id: str) -> bool:
        nid = uuid.UUID(notification_id)
        result = await self.db.execute(
            select(Notification).where(Notification.id == nid, Notification.recipient_id == uuid.UUID(user_id))
        )
        notification = result.scalar_one_or_none()
        if not notification:
            return False
        await self.db.delete(notification)
        await self.db.flush()
        return True
