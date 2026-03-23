"""Analytics schemas."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class DailyStatResponse(BaseModel):
    stat_date: date
    count: int = 0


class PlatformOverview(BaseModel):
    total_users: int = 0
    total_posts: int = 0
    total_comments: int = 0
    total_likes: int = 0
    total_stories: int = 0
    active_users_today: int = 0
    new_users_today: int = 0
    new_posts_today: int = 0


class UserGrowthResponse(BaseModel):
    period: str
    data: List[DailyStatResponse] = []


class ContentAnalyticsResponse(BaseModel):
    total_posts: int = 0
    total_comments: int = 0
    total_likes: int = 0
    posts_per_day: List[DailyStatResponse] = []
    engagement_rate: float = 0.0


class UserAnalyticsResponse(BaseModel):
    profile_views: int = 0
    post_impressions: int = 0
    total_likes_received: int = 0
    total_comments_received: int = 0
    follower_growth: List[DailyStatResponse] = []
    top_posts: list = []
