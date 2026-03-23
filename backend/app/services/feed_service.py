"""Feed service - generates personalized feeds for users."""

import uuid
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post, PostVisibility
from app.models.follow import Follow, FollowStatus
from app.models.block import Block
from app.models.mute import Mute


class FeedService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_home_feed(self, user_id: str, page: int = 1, page_size: int = 20):
        """Get a user's home feed: posts from people they follow + their own posts."""
        uid = uuid.UUID(user_id)

        # Get followed user IDs
        follow_result = await self.db.execute(
            select(Follow.following_id).where(
                Follow.follower_id == uid,
                Follow.status == FollowStatus.ACTIVE,
            )
        )
        following_ids = [row[0] for row in follow_result.all()]
        following_ids.append(uid)

        # Get blocked user IDs
        block_result = await self.db.execute(
            select(Block.blocked_id).where(Block.blocker_id == uid)
        )
        blocked_ids = [row[0] for row in block_result.all()]

        # Get muted user IDs
        mute_result = await self.db.execute(
            select(Mute.muted_user_id).where(Mute.user_id == uid)
        )
        muted_ids = [row[0] for row in mute_result.all()]

        exclude_ids = set(blocked_ids + muted_ids)

        query = select(Post).where(
            Post.author_id.in_(following_ids),
            Post.is_hidden == False,
            Post.is_archived == False,
            or_(
                Post.visibility == PostVisibility.PUBLIC,
                Post.visibility == PostVisibility.FOLLOWERS,
            ),
        )

        if exclude_ids:
            query = query.where(Post.author_id.notin_(exclude_ids))

        count_query = (
            select(func.count())
            .select_from(Post)
            .where(
                Post.author_id.in_(following_ids),
                Post.is_hidden == False,
                Post.is_archived == False,
            )
        )

        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_explore_feed(self, user_id: Optional[str] = None, page: int = 1, page_size: int = 20):
        """Get the explore/discover feed: trending public posts."""
        query = select(Post).where(
            Post.is_hidden == False,
            Post.is_archived == False,
            Post.visibility == PostVisibility.PUBLIC,
        )
        count_query = (
            select(func.count())
            .select_from(Post)
            .where(
                Post.is_hidden == False,
                Post.is_archived == False,
                Post.visibility == PostVisibility.PUBLIC,
            )
        )

        if user_id:
            uid = uuid.UUID(user_id)
            block_result = await self.db.execute(
                select(Block.blocked_id).where(Block.blocker_id == uid)
            )
            blocked_ids = [row[0] for row in block_result.all()]
            blocked_by_result = await self.db.execute(
                select(Block.blocker_id).where(Block.blocked_id == uid)
            )
            blocked_by_ids = [row[0] for row in blocked_by_result.all()]
            all_blocked = set(blocked_ids + blocked_by_ids)
            if all_blocked:
                query = query.where(Post.author_id.notin_(all_blocked))

        total = (await self.db.execute(count_query)).scalar() or 0
        # Order by engagement score (likes + comments + reposts)
        query = query.order_by(
            (Post.like_count + Post.comment_count + Post.repost_count).desc(),
            Post.created_at.desc(),
        ).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_hashtag_feed(self, hashtag_name: str, page: int = 1, page_size: int = 20):
        """Get posts for a specific hashtag."""
        from app.models.hashtag import Hashtag, PostHashtag

        result = await self.db.execute(select(Hashtag).where(Hashtag.name == hashtag_name.lower()))
        hashtag = result.scalar_one_or_none()
        if not hashtag:
            return [], 0

        query = (
            select(Post)
            .join(PostHashtag, PostHashtag.post_id == Post.id)
            .where(
                PostHashtag.hashtag_id == hashtag.id,
                Post.is_hidden == False,
                Post.visibility == PostVisibility.PUBLIC,
            )
        )
        count_query = (
            select(func.count())
            .select_from(PostHashtag)
            .where(PostHashtag.hashtag_id == hashtag.id)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total
