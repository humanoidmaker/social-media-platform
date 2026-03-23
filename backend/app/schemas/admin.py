"""Admin schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: Optional[str] = None
    role: str
    is_verified: bool = False
    is_active: bool = True
    is_banned: bool = False
    email_verified: bool = False
    follower_count: int = 0
    post_count: int = 0
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class AdminUpdateUserRequest(BaseModel):
    role: Optional[str] = Field(None, pattern=r"^(superadmin|admin|creator|user)$")
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None


class AdminPostResponse(BaseModel):
    id: str
    author_username: str
    content: Optional[str] = None
    post_type: str
    visibility: str
    like_count: int = 0
    comment_count: int = 0
    report_count: int = 0
    is_hidden: bool = False
    created_at: Optional[datetime] = None


class AdminReportResponse(BaseModel):
    id: str
    reporter_username: str
    target_type: str
    target_id: str
    reason: str
    description: Optional[str] = None
    status: str
    reviewed_by: Optional[str] = None
    resolution_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ResolveReportRequest(BaseModel):
    status: str = Field(pattern=r"^(resolved|dismissed)$")
    resolution_note: Optional[str] = Field(None, max_length=1000)
    action: Optional[str] = Field(None, pattern=r"^(none|warn|hide_content|ban_user)$")


class AdminDashboardResponse(BaseModel):
    total_users: int = 0
    total_posts: int = 0
    total_reports_pending: int = 0
    total_reports_today: int = 0
    new_users_today: int = 0
    new_posts_today: int = 0
    active_users_today: int = 0
    storage_used_mb: float = 0.0


class SystemHealthResponse(BaseModel):
    status: str = "healthy"
    database: str = "connected"
    redis: str = "connected"
    minio: str = "connected"
    celery_workers: int = 0
    uptime_seconds: float = 0.0


class AdminSettingsResponse(BaseModel):
    max_post_length: int = 2200
    max_comment_length: int = 1000
    max_media_per_post: int = 10
    story_expiration_hours: int = 24
    rate_limit_requests: int = 100
    maintenance_mode: bool = False


class UpdateAdminSettingsRequest(BaseModel):
    max_post_length: Optional[int] = None
    max_comment_length: Optional[int] = None
    max_media_per_post: Optional[int] = None
    story_expiration_hours: Optional[int] = None
    rate_limit_requests: Optional[int] = None
    maintenance_mode: Optional[bool] = None
