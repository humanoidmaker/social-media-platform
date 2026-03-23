"""Analytics service."""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.models.like import Like
from app.models.story import Story
from app.models.follow import Follow, FollowStatus
from app.models.report import Report, ReportStatus
from app.models.aggregate_stats import AggregateStats


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_platform_overview(self) -> dict:
        """Get overall platform statistics."""
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

        total_users = (await self.db.execute(select(func.count()).select_from(User))).scalar() or 0
        total_posts = (await self.db.execute(select(func.count()).select_from(Post))).scalar() or 0
        total_comments = (await self.db.execute(select(func.count()).select_from(Comment))).scalar() or 0
        total_likes = (await self.db.execute(select(func.count()).select_from(Like))).scalar() or 0
        total_stories = (await self.db.execute(select(func.count()).select_from(Story))).scalar() or 0

        new_users_today = (
            await self.db.execute(
                select(func.count()).select_from(User).where(User.created_at >= today_start)
            )
        ).scalar() or 0

        new_posts_today = (
            await self.db.execute(
                select(func.count()).select_from(Post).where(Post.created_at >= today_start)
            )
        ).scalar() or 0

        active_users_today = (
            await self.db.execute(
                select(func.count()).select_from(User).where(User.last_login_at >= today_start)
            )
        ).scalar() or 0

        return {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_likes": total_likes,
            "total_stories": total_stories,
            "active_users_today": active_users_today,
            "new_users_today": new_users_today,
            "new_posts_today": new_posts_today,
        }

    async def get_user_growth(self, days: int = 30) -> list[dict]:
        """Get daily user registration counts for the past N days."""
        stats = []
        today = datetime.now(timezone.utc).date()
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = datetime.combine(day + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)
            count = (
                await self.db.execute(
                    select(func.count()).select_from(User).where(
                        User.created_at >= day_start, User.created_at < day_end
                    )
                )
            ).scalar() or 0
            stats.append({"stat_date": day, "count": count})
        return stats

    async def get_content_analytics(self, days: int = 30) -> dict:
        """Get content creation analytics."""
        today = datetime.now(timezone.utc).date()
        period_start = datetime.combine(
            today - timedelta(days=days), datetime.min.time()
        ).replace(tzinfo=timezone.utc)

        total_posts = (
            await self.db.execute(
                select(func.count()).select_from(Post).where(Post.created_at >= period_start)
            )
        ).scalar() or 0
        total_comments = (
            await self.db.execute(
                select(func.count()).select_from(Comment).where(Comment.created_at >= period_start)
            )
        ).scalar() or 0
        total_likes = (
            await self.db.execute(
                select(func.count()).select_from(Like).where(Like.created_at >= period_start)
            )
        ).scalar() or 0

        posts_per_day = []
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = datetime.combine(day + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)
            count = (
                await self.db.execute(
                    select(func.count()).select_from(Post).where(
                        Post.created_at >= day_start, Post.created_at < day_end
                    )
                )
            ).scalar() or 0
            posts_per_day.append({"stat_date": day, "count": count})

        engagement_rate = 0.0
        if total_posts > 0:
            engagement_rate = round((total_likes + total_comments) / total_posts, 2)

        return {
            "total_posts": total_posts,
            "total_comments": total_comments,
            "total_likes": total_likes,
            "posts_per_day": posts_per_day,
            "engagement_rate": engagement_rate,
        }

    async def get_user_analytics(self, user_id: str) -> dict:
        """Get analytics for a specific user's content."""
        uid = uuid.UUID(user_id)

        total_likes = (
            await self.db.execute(
                select(func.sum(Post.like_count)).where(Post.author_id == uid)
            )
        ).scalar() or 0

        total_comments = (
            await self.db.execute(
                select(func.sum(Post.comment_count)).where(Post.author_id == uid)
            )
        ).scalar() or 0

        total_views = (
            await self.db.execute(
                select(func.sum(Post.view_count)).where(Post.author_id == uid)
            )
        ).scalar() or 0

        # Follower growth over last 30 days
        today = datetime.now(timezone.utc).date()
        follower_growth = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = datetime.combine(day + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)
            count = (
                await self.db.execute(
                    select(func.count()).select_from(Follow).where(
                        Follow.following_id == uid,
                        Follow.status == FollowStatus.ACTIVE,
                        Follow.created_at >= day_start,
                        Follow.created_at < day_end,
                    )
                )
            ).scalar() or 0
            follower_growth.append({"stat_date": day, "count": count})

        # Top posts
        top_posts_result = await self.db.execute(
            select(Post)
            .where(Post.author_id == uid, Post.is_hidden == False)
            .order_by((Post.like_count + Post.comment_count).desc())
            .limit(5)
        )
        top_posts = [
            {"id": str(p.id), "content": (p.content or "")[:100], "likes": p.like_count, "comments": p.comment_count}
            for p in top_posts_result.scalars().all()
        ]

        return {
            "profile_views": 0,
            "post_impressions": total_views,
            "total_likes_received": total_likes,
            "total_comments_received": total_comments,
            "follower_growth": follower_growth,
            "top_posts": top_posts,
        }

    async def get_admin_dashboard(self) -> dict:
        """Get admin dashboard statistics."""
        overview = await self.get_platform_overview()
        pending_reports = (
            await self.db.execute(
                select(func.count()).select_from(Report).where(Report.status == ReportStatus.PENDING)
            )
        ).scalar() or 0

        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        reports_today = (
            await self.db.execute(
                select(func.count()).select_from(Report).where(Report.created_at >= today_start)
            )
        ).scalar() or 0

        return {
            **overview,
            "total_reports_pending": pending_reports,
            "total_reports_today": reports_today,
            "storage_used_mb": 0.0,
        }

    async def save_daily_stats(self) -> None:
        """Aggregate and save daily stats."""
        today = date.today()
        overview = await self.get_platform_overview()

        for stat_type, count in [
            ("total_users", overview["total_users"]),
            ("total_posts", overview["total_posts"]),
            ("new_users", overview["new_users_today"]),
            ("new_posts", overview["new_posts_today"]),
            ("active_users", overview["active_users_today"]),
        ]:
            stat = AggregateStats(stat_date=today, stat_type=stat_type, count=count)
            self.db.add(stat)

        await self.db.flush()
