"""User schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserPublicResponse(BaseModel):
    id: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    is_verified: bool = False
    is_private: bool = False
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserDetailResponse(UserPublicResponse):
    email: str
    role: str
    is_active: bool = True
    email_verified: bool = False
    last_login_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    is_private: Optional[bool] = None


class UpdateEmailRequest(BaseModel):
    email: EmailStr


class FollowResponse(BaseModel):
    id: str
    follower_id: str
    following_id: str
    status: str
    created_at: Optional[datetime] = None


class BlockResponse(BaseModel):
    id: str
    blocker_id: str
    blocked_id: str
    created_at: Optional[datetime] = None


class UserListItem(BaseModel):
    id: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool = False


class FollowRequestResponse(BaseModel):
    id: str
    follower: UserListItem
    created_at: Optional[datetime] = None
