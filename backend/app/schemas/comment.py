"""Comment schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserListItem


class CommentResponse(BaseModel):
    id: str
    post_id: str
    author: UserListItem
    parent_id: Optional[str] = None
    content: str
    like_count: int = 0
    reply_count: int = 0
    is_liked: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreateCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    parent_id: Optional[str] = None


class UpdateCommentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class CommentListResponse(BaseModel):
    items: List[CommentResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False
