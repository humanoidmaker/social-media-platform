"""Story schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserListItem


class StoryResponse(BaseModel):
    id: str
    author: UserListItem
    media_type: str
    media_url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    duration_seconds: int = 5
    view_count: int = 0
    is_close_friends: bool = False
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    has_viewed: bool = False


class StoryGroupResponse(BaseModel):
    user: UserListItem
    stories: List[StoryResponse] = []
    has_unseen: bool = False


class CreateStoryRequest(BaseModel):
    caption: Optional[str] = Field(None, max_length=500)
    duration_seconds: int = Field(default=5, ge=1, le=60)
    is_close_friends: bool = False


class StoryViewerResponse(BaseModel):
    viewer: UserListItem
    viewed_at: Optional[datetime] = None


class StoryHighlightResponse(BaseModel):
    id: str
    title: str
    cover_url: Optional[str] = None
    story_ids: List[str] = []
    created_at: Optional[datetime] = None


class CreateHighlightRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    story_ids: List[str] = []


class UpdateHighlightRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    story_ids: Optional[List[str]] = None
