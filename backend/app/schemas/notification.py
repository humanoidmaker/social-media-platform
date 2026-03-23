"""Notification schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.user import UserListItem


class NotificationResponse(BaseModel):
    id: str
    notification_type: str
    title: str
    body: Optional[str] = None
    actor: Optional[UserListItem] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse] = []
    total: int = 0
    unread_count: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False


class MarkReadRequest(BaseModel):
    notification_ids: List[str] = []
