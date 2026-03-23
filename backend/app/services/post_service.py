"""Post service."""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post, PostType, PostVisibility
from app.models.post_media import PostMedia
from app.models.like import Like
from app.models.bookmark import Bookmark
from app.models.comment import Comment
from app.models.poll import Poll
from app.models.poll_option import PollOption
from app.models.poll_vote import PollVote
from app.models.hashtag import Hashtag, PostHashtag
from app.models.user import User


class PostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, post_id: str) -> Optional[Post]:
        pid = uuid.UUID(post_id) if isinstance(post_id, str) else post_id
        result = await self.db.execute(select(Post).where(Post.id == pid))
        return result.scalar_one_or_none()

    async def create(
        self,
        author_id: str,
        content: Optional[str],
        post_type: str = "text",
        visibility: str = "public",
        location: Optional[str] = None,
        is_comments_disabled: bool = False,
        poll_options: Optional[list[str]] = None,
        poll_expires_hours: Optional[int] = None,
    ) -> Post:
        aid = uuid.UUID(author_id)
        post = Post(
            author_id=aid,
            content=content,
            post_type=PostType(post_type),
            visibility=PostVisibility(visibility),
            location=location,
            is_comments_disabled=is_comments_disabled,
        )
        self.db.add(post)
        await self.db.flush()

        # Create poll if specified
        if post_type == "poll" and poll_options:
            post.post_type = PostType.POLL
            expires_at = None
            if poll_expires_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=poll_expires_hours)
            poll = Poll(post_id=post.id, expires_at=expires_at)
            self.db.add(poll)
            await self.db.flush()
            for i, option_text in enumerate(poll_options):
                option = PollOption(poll_id=poll.id, text=option_text, sort_order=i)
                self.db.add(option)

        # Extract and link hashtags from content
        if content:
            await self._process_hashtags(post.id, content)

        # Update user post count
        result = await self.db.execute(select(User).where(User.id == aid))
        user = result.scalar_one_or_none()
        if user:
            user.post_count += 1

        await self.db.flush()
        return post

    async def _process_hashtags(self, post_id: uuid.UUID, content: str) -> None:
        """Extract hashtags from content and create/link them."""
        hashtag_names = set(re.findall(r"#(\w+)", content))
        for name in hashtag_names:
            name_lower = name.lower()
            result = await self.db.execute(select(Hashtag).where(Hashtag.name == name_lower))
            hashtag = result.scalar_one_or_none()
            if not hashtag:
                hashtag = Hashtag(name=name_lower)
                self.db.add(hashtag)
                await self.db.flush()

            hashtag.post_count += 1
            link = PostHashtag(post_id=post_id, hashtag_id=hashtag.id)
            self.db.add(link)

    async def update(self, post_id: str, author_id: str, **kwargs) -> Optional[Post]:
        post = await self.get_by_id(post_id)
        if not post or str(post.author_id) != author_id:
            return None
        for key, value in kwargs.items():
            if hasattr(post, key) and value is not None:
                if key == "visibility":
                    setattr(post, key, PostVisibility(value))
                else:
                    setattr(post, key, value)
        await self.db.flush()
        return post

    async def delete(self, post_id: str, author_id: str, is_admin: bool = False) -> bool:
        post = await self.get_by_id(post_id)
        if not post:
            return False
        if not is_admin and str(post.author_id) != author_id:
            return False

        # Decrement user post count
        result = await self.db.execute(select(User).where(User.id == post.author_id))
        user = result.scalar_one_or_none()
        if user:
            user.post_count = max(0, user.post_count - 1)

        await self.db.delete(post)
        await self.db.flush()
        return True

    async def like_post(self, user_id: str, post_id: str) -> bool:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)
        existing = await self.db.execute(
            select(Like).where(Like.user_id == uid, Like.post_id == pid)
        )
        if existing.scalar_one_or_none():
            return False

        like = Like(user_id=uid, post_id=pid)
        self.db.add(like)

        post = await self.get_by_id(post_id)
        if post:
            post.like_count += 1

        await self.db.flush()
        return True

    async def unlike_post(self, user_id: str, post_id: str) -> bool:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)
        result = await self.db.execute(
            select(Like).where(Like.user_id == uid, Like.post_id == pid)
        )
        like = result.scalar_one_or_none()
        if not like:
            return False

        await self.db.delete(like)
        post = await self.get_by_id(post_id)
        if post:
            post.like_count = max(0, post.like_count - 1)

        await self.db.flush()
        return True

    async def bookmark_post(self, user_id: str, post_id: str, collection_id: Optional[str] = None) -> bool:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)
        existing = await self.db.execute(
            select(Bookmark).where(Bookmark.user_id == uid, Bookmark.post_id == pid)
        )
        if existing.scalar_one_or_none():
            return False

        cid = uuid.UUID(collection_id) if collection_id else None
        bookmark = Bookmark(user_id=uid, post_id=pid, collection_id=cid)
        self.db.add(bookmark)

        post = await self.get_by_id(post_id)
        if post:
            post.bookmark_count += 1

        await self.db.flush()
        return True

    async def unbookmark_post(self, user_id: str, post_id: str) -> bool:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.user_id == uid, Bookmark.post_id == pid)
        )
        bookmark = result.scalar_one_or_none()
        if not bookmark:
            return False

        await self.db.delete(bookmark)
        post = await self.get_by_id(post_id)
        if post:
            post.bookmark_count = max(0, post.bookmark_count - 1)

        await self.db.flush()
        return True

    async def repost(self, user_id: str, original_post_id: str, quote_content: Optional[str] = None) -> Optional[Post]:
        uid = uuid.UUID(user_id)
        original = await self.get_by_id(original_post_id)
        if not original:
            return None

        repost = Post(
            author_id=uid,
            content=quote_content,
            post_type=PostType.REPOST,
            repost_of_id=original.id,
            quote_content=quote_content,
        )
        self.db.add(repost)
        original.repost_count += 1

        result = await self.db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if user:
            user.post_count += 1

        await self.db.flush()
        return repost

    async def add_comment(self, post_id: str, author_id: str, content: str, parent_id: Optional[str] = None) -> Comment:
        pid = uuid.UUID(post_id)
        aid = uuid.UUID(author_id)
        prid = uuid.UUID(parent_id) if parent_id else None

        comment = Comment(post_id=pid, author_id=aid, content=content, parent_id=prid)
        self.db.add(comment)

        post = await self.get_by_id(post_id)
        if post:
            post.comment_count += 1

        if parent_id:
            parent_result = await self.db.execute(select(Comment).where(Comment.id == prid))
            parent = parent_result.scalar_one_or_none()
            if parent:
                parent.reply_count += 1

        await self.db.flush()
        return comment

    async def update_comment(self, comment_id: str, author_id: str, content: str) -> Optional[Comment]:
        cid = uuid.UUID(comment_id)
        result = await self.db.execute(select(Comment).where(Comment.id == cid))
        comment = result.scalar_one_or_none()
        if not comment or str(comment.author_id) != author_id:
            return None
        comment.content = content
        await self.db.flush()
        return comment

    async def delete_comment(self, comment_id: str, user_id: str, is_admin: bool = False) -> bool:
        cid = uuid.UUID(comment_id)
        result = await self.db.execute(select(Comment).where(Comment.id == cid))
        comment = result.scalar_one_or_none()
        if not comment:
            return False
        if not is_admin and str(comment.author_id) != user_id:
            return False

        post = await self.get_by_id(str(comment.post_id))
        if post:
            post.comment_count = max(0, post.comment_count - 1)

        if comment.parent_id:
            parent_result = await self.db.execute(select(Comment).where(Comment.id == comment.parent_id))
            parent = parent_result.scalar_one_or_none()
            if parent:
                parent.reply_count = max(0, parent.reply_count - 1)

        await self.db.delete(comment)
        await self.db.flush()
        return True

    async def get_post_comments(self, post_id: str, page: int = 1, page_size: int = 20, parent_id: Optional[str] = None):
        pid = uuid.UUID(post_id)
        query = select(Comment).where(Comment.post_id == pid)
        count_query = select(func.count()).select_from(Comment).where(Comment.post_id == pid)

        if parent_id:
            prid = uuid.UUID(parent_id)
            query = query.where(Comment.parent_id == prid)
            count_query = count_query.where(Comment.parent_id == prid)
        else:
            query = query.where(Comment.parent_id.is_(None))
            count_query = count_query.where(Comment.parent_id.is_(None))

        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Comment.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def like_comment(self, user_id: str, comment_id: str) -> bool:
        uid = uuid.UUID(user_id)
        cid = uuid.UUID(comment_id)
        existing = await self.db.execute(
            select(Like).where(Like.user_id == uid, Like.comment_id == cid)
        )
        if existing.scalar_one_or_none():
            return False

        like = Like(user_id=uid, comment_id=cid)
        self.db.add(like)

        result = await self.db.execute(select(Comment).where(Comment.id == cid))
        comment = result.scalar_one_or_none()
        if comment:
            comment.like_count += 1

        await self.db.flush()
        return True

    async def unlike_comment(self, user_id: str, comment_id: str) -> bool:
        uid = uuid.UUID(user_id)
        cid = uuid.UUID(comment_id)
        result = await self.db.execute(
            select(Like).where(Like.user_id == uid, Like.comment_id == cid)
        )
        like = result.scalar_one_or_none()
        if not like:
            return False

        await self.db.delete(like)

        comment_result = await self.db.execute(select(Comment).where(Comment.id == cid))
        comment = comment_result.scalar_one_or_none()
        if comment:
            comment.like_count = max(0, comment.like_count - 1)

        await self.db.flush()
        return True

    async def vote_poll(self, user_id: str, post_id: str, option_id: str) -> bool:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)
        oid = uuid.UUID(option_id)

        post = await self.get_by_id(post_id)
        if not post or not post.poll:
            return False

        poll = post.poll
        if poll.expires_at and poll.expires_at < datetime.now(timezone.utc):
            return False

        existing = await self.db.execute(
            select(PollVote).where(PollVote.poll_id == poll.id, PollVote.user_id == uid)
        )
        if existing.scalar_one_or_none():
            return False

        vote = PollVote(poll_id=poll.id, option_id=oid, user_id=uid)
        self.db.add(vote)
        poll.total_votes += 1

        option_result = await self.db.execute(select(PollOption).where(PollOption.id == oid))
        option = option_result.scalar_one_or_none()
        if option:
            option.vote_count += 1

        await self.db.flush()
        return True

    async def get_user_posts(self, user_id: str, page: int = 1, page_size: int = 20):
        uid = uuid.UUID(user_id)
        query = select(Post).where(Post.author_id == uid, Post.is_hidden == False, Post.is_archived == False)
        count_query = (
            select(func.count())
            .select_from(Post)
            .where(Post.author_id == uid, Post.is_hidden == False, Post.is_archived == False)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Post.is_pinned.desc(), Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_user_bookmarks(self, user_id: str, page: int = 1, page_size: int = 20, collection_id: Optional[str] = None):
        uid = uuid.UUID(user_id)
        query = (
            select(Post)
            .join(Bookmark, Bookmark.post_id == Post.id)
            .where(Bookmark.user_id == uid)
        )
        count_query = select(func.count()).select_from(Bookmark).where(Bookmark.user_id == uid)

        if collection_id:
            cid = uuid.UUID(collection_id)
            query = query.where(Bookmark.collection_id == cid)
            count_query = count_query.where(Bookmark.collection_id == cid)

        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Bookmark.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_post_likes(self, post_id: str, page: int = 1, page_size: int = 20):
        pid = uuid.UUID(post_id)
        query = (
            select(User)
            .join(Like, Like.user_id == User.id)
            .where(Like.post_id == pid)
        )
        count_query = select(func.count()).select_from(Like).where(Like.post_id == pid)
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Like.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def is_liked(self, user_id: str, post_id: str) -> bool:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)
        result = await self.db.execute(
            select(Like).where(Like.user_id == uid, Like.post_id == pid)
        )
        return result.scalar_one_or_none() is not None

    async def is_bookmarked(self, user_id: str, post_id: str) -> bool:
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(post_id)
        result = await self.db.execute(
            select(Bookmark).where(Bookmark.user_id == uid, Bookmark.post_id == pid)
        )
        return result.scalar_one_or_none() is not None

    async def pin_post(self, post_id: str, author_id: str) -> bool:
        post = await self.get_by_id(post_id)
        if not post or str(post.author_id) != author_id:
            return False
        # Unpin other posts
        aid = uuid.UUID(author_id)
        result = await self.db.execute(
            select(Post).where(Post.author_id == aid, Post.is_pinned == True)
        )
        for p in result.scalars().all():
            p.is_pinned = False
        post.is_pinned = True
        await self.db.flush()
        return True

    async def unpin_post(self, post_id: str, author_id: str) -> bool:
        post = await self.get_by_id(post_id)
        if not post or str(post.author_id) != author_id:
            return False
        post.is_pinned = False
        await self.db.flush()
        return True

    async def hide_post(self, post_id: str) -> bool:
        """Admin: hide a post."""
        post = await self.get_by_id(post_id)
        if not post:
            return False
        post.is_hidden = True
        await self.db.flush()
        return True

    async def unhide_post(self, post_id: str) -> bool:
        """Admin: unhide a post."""
        post = await self.get_by_id(post_id)
        if not post:
            return False
        post.is_hidden = False
        await self.db.flush()
        return True

    async def list_posts_admin(self, page: int = 1, page_size: int = 20, search: Optional[str] = None):
        query = select(Post)
        count_query = select(func.count()).select_from(Post)
        if search:
            query = query.where(Post.content.ilike(f"%{search}%"))
            count_query = count_query.where(Post.content.ilike(f"%{search}%"))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def increment_view(self, post_id: str) -> None:
        post = await self.get_by_id(post_id)
        if post:
            post.view_count += 1
            await self.db.flush()
