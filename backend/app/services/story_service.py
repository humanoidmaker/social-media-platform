"""Story service."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.story import Story, StoryMediaType
from app.models.story_view import StoryView
from app.models.story_highlight import StoryHighlight
from app.models.follow import Follow, FollowStatus
from app.models.block import Block
from app.models.close_friend import CloseFriend


class StoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        author_id: str,
        media_type: str,
        media_url: str,
        media_key: str,
        caption: Optional[str] = None,
        duration_seconds: int = 5,
        is_close_friends: bool = False,
        thumbnail_url: Optional[str] = None,
    ) -> Story:
        aid = uuid.UUID(author_id)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.STORY_EXPIRATION_HOURS)
        story = Story(
            author_id=aid,
            media_type=StoryMediaType(media_type),
            media_url=media_url,
            media_key=media_key,
            thumbnail_url=thumbnail_url,
            caption=caption,
            duration_seconds=duration_seconds,
            is_close_friends=is_close_friends,
            expires_at=expires_at,
        )
        self.db.add(story)
        await self.db.flush()
        return story

    async def get_by_id(self, story_id: str) -> Optional[Story]:
        sid = uuid.UUID(story_id)
        result = await self.db.execute(select(Story).where(Story.id == sid))
        return result.scalar_one_or_none()

    async def delete(self, story_id: str, author_id: str) -> bool:
        story = await self.get_by_id(story_id)
        if not story or str(story.author_id) != author_id:
            return False
        await self.db.delete(story)
        await self.db.flush()
        return True

    async def view_story(self, story_id: str, viewer_id: str) -> bool:
        sid = uuid.UUID(story_id)
        vid = uuid.UUID(viewer_id)

        existing = await self.db.execute(
            select(StoryView).where(StoryView.story_id == sid, StoryView.viewer_id == vid)
        )
        if existing.scalar_one_or_none():
            return False

        view = StoryView(story_id=sid, viewer_id=vid)
        self.db.add(view)

        story = await self.get_by_id(story_id)
        if story:
            story.view_count += 1

        await self.db.flush()
        return True

    async def get_story_viewers(self, story_id: str, page: int = 1, page_size: int = 20):
        sid = uuid.UUID(story_id)
        query = select(StoryView).where(StoryView.story_id == sid).order_by(StoryView.viewed_at.desc())
        count_query = select(func.count()).select_from(StoryView).where(StoryView.story_id == sid)
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_feed_stories(self, user_id: str):
        """Get active stories from users the current user follows, grouped by author."""
        uid = uuid.UUID(user_id)
        now = datetime.now(timezone.utc)

        # Get followed user IDs
        follow_result = await self.db.execute(
            select(Follow.following_id).where(
                Follow.follower_id == uid,
                Follow.status == FollowStatus.ACTIVE,
            )
        )
        following_ids = [row[0] for row in follow_result.all()]
        following_ids.append(uid)

        # Get blocked users
        block_result = await self.db.execute(
            select(Block.blocked_id).where(Block.blocker_id == uid)
        )
        blocked_ids = set(row[0] for row in block_result.all())

        # Get close friends list for the current user
        close_friend_result = await self.db.execute(
            select(CloseFriend.user_id).where(CloseFriend.friend_id == uid)
        )
        close_friend_of = set(row[0] for row in close_friend_result.all())

        query = select(Story).where(
            Story.author_id.in_(following_ids),
            Story.is_active == True,
            Story.expires_at > now,
        )
        if blocked_ids:
            query = query.where(Story.author_id.notin_(blocked_ids))

        query = query.order_by(Story.created_at.desc())
        result = await self.db.execute(query)
        stories = result.scalars().all()

        # Filter close friends stories
        filtered = []
        for story in stories:
            if story.is_close_friends:
                if story.author_id in close_friend_of or str(story.author_id) == user_id:
                    filtered.append(story)
            else:
                filtered.append(story)

        # Group by author
        grouped: dict[str, list] = {}
        for story in filtered:
            author_key = str(story.author_id)
            if author_key not in grouped:
                grouped[author_key] = []
            grouped[author_key].append(story)

        return grouped

    async def get_user_stories(self, user_id: str):
        """Get active stories for a specific user."""
        uid = uuid.UUID(user_id)
        now = datetime.now(timezone.utc)
        query = select(Story).where(
            Story.author_id == uid,
            Story.is_active == True,
            Story.expires_at > now,
        ).order_by(Story.created_at.asc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def expire_stories(self) -> int:
        """Mark expired stories as inactive. Returns count of expired stories."""
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Story).where(Story.is_active == True, Story.expires_at <= now)
        )
        stories = result.scalars().all()
        for story in stories:
            story.is_active = False
        await self.db.flush()
        return len(stories)

    # Highlights
    async def create_highlight(self, user_id: str, title: str, story_ids: list[str]) -> StoryHighlight:
        uid = uuid.UUID(user_id)
        sids = [uuid.UUID(sid) for sid in story_ids]
        highlight = StoryHighlight(user_id=uid, title=title, story_ids=sids)
        self.db.add(highlight)
        await self.db.flush()
        return highlight

    async def get_user_highlights(self, user_id: str):
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(StoryHighlight).where(StoryHighlight.user_id == uid).order_by(StoryHighlight.created_at.desc())
        )
        return result.scalars().all()

    async def update_highlight(self, highlight_id: str, user_id: str, **kwargs) -> Optional[StoryHighlight]:
        hid = uuid.UUID(highlight_id)
        result = await self.db.execute(select(StoryHighlight).where(StoryHighlight.id == hid))
        highlight = result.scalar_one_or_none()
        if not highlight or str(highlight.user_id) != user_id:
            return None
        for key, value in kwargs.items():
            if hasattr(highlight, key) and value is not None:
                if key == "story_ids":
                    setattr(highlight, key, [uuid.UUID(s) for s in value])
                else:
                    setattr(highlight, key, value)
        await self.db.flush()
        return highlight

    async def delete_highlight(self, highlight_id: str, user_id: str) -> bool:
        hid = uuid.UUID(highlight_id)
        result = await self.db.execute(select(StoryHighlight).where(StoryHighlight.id == hid))
        highlight = result.scalar_one_or_none()
        if not highlight or str(highlight.user_id) != user_id:
            return False
        await self.db.delete(highlight)
        await self.db.flush()
        return True
