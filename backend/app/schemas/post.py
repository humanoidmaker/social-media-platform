"""Post schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserListItem


class PostMediaResponse(BaseModel):
    id: str
    media_type: str
    url: str
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[int] = None
    alt_text: Optional[str] = None
    sort_order: int = 0


class PollOptionResponse(BaseModel):
    id: str
    text: str
    vote_count: int = 0
    sort_order: int = 0


class PollResponse(BaseModel):
    id: str
    total_votes: int = 0
    expires_at: Optional[datetime] = None
    options: List[PollOptionResponse] = []
    user_voted_option_id: Optional[str] = None


class PostResponse(BaseModel):
    id: str
    author: UserListItem
    content: Optional[str] = None
    post_type: str
    visibility: str
    location: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    repost_count: int = 0
    bookmark_count: int = 0
    view_count: int = 0
    is_pinned: bool = False
    is_comments_disabled: bool = False
    media: List[PostMediaResponse] = []
    poll: Optional[PollResponse] = None
    original_post: Optional["PostResponse"] = None
    is_liked: bool = False
    is_bookmarked: bool = False
    is_reposted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreatePostRequest(BaseModel):
    content: Optional[str] = Field(None, max_length=2200)
    post_type: str = Field(default="text", pattern=r"^(text|image|video|carousel|poll)$")
    visibility: str = Field(default="public", pattern=r"^(public|followers|close_friends|private)$")
    location: Optional[str] = Field(None, max_length=200)
    is_comments_disabled: bool = False
    poll_options: Optional[List[str]] = None
    poll_expires_hours: Optional[int] = Field(None, ge=1, le=168)


class UpdatePostRequest(BaseModel):
    content: Optional[str] = Field(None, max_length=2200)
    visibility: Optional[str] = Field(None, pattern=r"^(public|followers|close_friends|private)$")
    location: Optional[str] = Field(None, max_length=200)
    is_comments_disabled: Optional[bool] = None


class RepostRequest(BaseModel):
    quote_content: Optional[str] = Field(None, max_length=2200)


class PollVoteRequest(BaseModel):
    option_id: str
