"""Search service."""

import uuid
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.post import Post, PostVisibility
from app.models.hashtag import Hashtag


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_users(self, query: str, page: int = 1, page_size: int = 20):
        search_filter = or_(
            User.username.ilike(f"%{query}%"),
            User.display_name.ilike(f"%{query}%"),
        )
        db_query = (
            select(User)
            .where(search_filter, User.is_active == True, User.is_banned == False)
            .order_by(User.follower_count.desc())
        )
        count_query = (
            select(func.count())
            .select_from(User)
            .where(search_filter, User.is_active == True, User.is_banned == False)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        db_query = db_query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(db_query)
        return result.scalars().all(), total

    async def search_posts(self, query: str, page: int = 1, page_size: int = 20):
        search_filter = Post.content.ilike(f"%{query}%")
        db_query = (
            select(Post)
            .where(
                search_filter,
                Post.is_hidden == False,
                Post.visibility == PostVisibility.PUBLIC,
            )
            .order_by(Post.like_count.desc(), Post.created_at.desc())
        )
        count_query = (
            select(func.count())
            .select_from(Post)
            .where(
                search_filter,
                Post.is_hidden == False,
                Post.visibility == PostVisibility.PUBLIC,
            )
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        db_query = db_query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(db_query)
        return result.scalars().all(), total

    async def search_hashtags(self, query: str, page: int = 1, page_size: int = 20):
        search_filter = Hashtag.name.ilike(f"%{query}%")
        db_query = (
            select(Hashtag)
            .where(search_filter)
            .order_by(Hashtag.post_count.desc())
        )
        count_query = (
            select(func.count())
            .select_from(Hashtag)
            .where(search_filter)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        db_query = db_query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(db_query)
        return result.scalars().all(), total

    async def search_all(self, query: str, page: int = 1, page_size: int = 10):
        """Search across users, posts, and hashtags."""
        users, total_users = await self.search_users(query, page, page_size)
        posts, total_posts = await self.search_posts(query, page, page_size)
        hashtags, total_hashtags = await self.search_hashtags(query, page, page_size)
        return {
            "users": users,
            "posts": posts,
            "hashtags": hashtags,
            "total_users": total_users,
            "total_posts": total_posts,
            "total_hashtags": total_hashtags,
        }

    async def get_trending_hashtags(self, limit: int = 20):
        """Get trending hashtags ordered by post count."""
        result = await self.db.execute(
            select(Hashtag).order_by(Hashtag.post_count.desc()).limit(limit)
        )
        return result.scalars().all()

    async def get_suggested_users(self, user_id: Optional[str] = None, limit: int = 20):
        """Get suggested users based on popularity."""
        query = (
            select(User)
            .where(User.is_active == True, User.is_banned == False)
            .order_by(User.follower_count.desc())
            .limit(limit)
        )
        if user_id:
            uid = uuid.UUID(user_id)
            query = query.where(User.id != uid)
        result = await self.db.execute(query)
        return result.scalars().all()
