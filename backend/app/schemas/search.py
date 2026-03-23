"""Search schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.post import PostResponse
from app.schemas.user import UserListItem


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    search_type: str = Field(default="all", pattern=r"^(all|users|posts|hashtags)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class HashtagSearchResult(BaseModel):
    id: str
    name: str
    post_count: int = 0


class SearchResponse(BaseModel):
    users: List[UserListItem] = []
    posts: List[PostResponse] = []
    hashtags: List[HashtagSearchResult] = []
    total_users: int = 0
    total_posts: int = 0
    total_hashtags: int = 0
