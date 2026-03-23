"""User service."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.follow import Follow, FollowStatus
from app.models.block import Block
from app.utils.hashing import hash_password, verify_password
from app.utils.tokens import generate_random_token


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[User]:
        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        result = await self.db.execute(select(User).where(User.id == uid))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username.lower()))
        return result.scalar_one_or_none()

    async def create(self, username: str, email: str, password: str, display_name: str) -> User:
        user = User(
            username=username.lower(),
            email=email.lower(),
            password_hash=hash_password(password),
            display_name=display_name,
            email_verification_token=generate_random_token(),
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            return None
        if not user.is_active or user.is_banned:
            return None
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user

    async def verify_email(self, token: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email_verification_token == token)
        )
        user = result.scalar_one_or_none()
        if user:
            user.email_verified = True
            user.email_verification_token = None
            await self.db.flush()
        return user

    async def request_password_reset(self, email: str) -> Optional[str]:
        user = await self.get_by_email(email)
        if not user:
            return None
        token = generate_random_token()
        user.password_reset_token = token
        user.password_reset_expires = datetime.now(timezone.utc)
        await self.db.flush()
        return token

    async def reset_password(self, token: str, new_password: str) -> bool:
        result = await self.db.execute(
            select(User).where(User.password_reset_token == token)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        await self.db.flush()
        return True

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        user = await self.get_by_id(user_id)
        if not user or not verify_password(current_password, user.password_hash):
            return False
        user.password_hash = hash_password(new_password)
        await self.db.flush()
        return True

    async def update_profile(self, user_id: str, **kwargs) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        await self.db.flush()
        return user

    async def follow_user(self, follower_id: str, following_id: str) -> Optional[Follow]:
        if follower_id == following_id:
            return None
        fid = uuid.UUID(follower_id)
        tid = uuid.UUID(following_id)

        # Check if blocked
        block_check = await self.db.execute(
            select(Block).where(
                or_(
                    (Block.blocker_id == fid) & (Block.blocked_id == tid),
                    (Block.blocker_id == tid) & (Block.blocked_id == fid),
                )
            )
        )
        if block_check.scalar_one_or_none():
            return None

        # Check existing follow
        existing = await self.db.execute(
            select(Follow).where(Follow.follower_id == fid, Follow.following_id == tid)
        )
        if existing.scalar_one_or_none():
            return None

        target_user = await self.get_by_id(following_id)
        if not target_user:
            return None

        status = FollowStatus.PENDING if target_user.is_private else FollowStatus.ACTIVE
        follow = Follow(follower_id=fid, following_id=tid, status=status)
        self.db.add(follow)

        if status == FollowStatus.ACTIVE:
            target_user.follower_count += 1
            follower = await self.get_by_id(follower_id)
            if follower:
                follower.following_count += 1

        await self.db.flush()
        return follow

    async def unfollow_user(self, follower_id: str, following_id: str) -> bool:
        fid = uuid.UUID(follower_id)
        tid = uuid.UUID(following_id)
        result = await self.db.execute(
            select(Follow).where(Follow.follower_id == fid, Follow.following_id == tid)
        )
        follow = result.scalar_one_or_none()
        if not follow:
            return False

        was_active = follow.status == FollowStatus.ACTIVE
        await self.db.delete(follow)

        if was_active:
            target_user = await self.get_by_id(following_id)
            if target_user:
                target_user.follower_count = max(0, target_user.follower_count - 1)
            follower = await self.get_by_id(follower_id)
            if follower:
                follower.following_count = max(0, follower.following_count - 1)

        await self.db.flush()
        return True

    async def accept_follow_request(self, user_id: str, follower_id: str) -> bool:
        uid = uuid.UUID(user_id)
        fid = uuid.UUID(follower_id)
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == fid,
                Follow.following_id == uid,
                Follow.status == FollowStatus.PENDING,
            )
        )
        follow = result.scalar_one_or_none()
        if not follow:
            return False

        follow.status = FollowStatus.ACTIVE
        user = await self.get_by_id(user_id)
        if user:
            user.follower_count += 1
        follower = await self.get_by_id(follower_id)
        if follower:
            follower.following_count += 1

        await self.db.flush()
        return True

    async def reject_follow_request(self, user_id: str, follower_id: str) -> bool:
        uid = uuid.UUID(user_id)
        fid = uuid.UUID(follower_id)
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == fid,
                Follow.following_id == uid,
                Follow.status == FollowStatus.PENDING,
            )
        )
        follow = result.scalar_one_or_none()
        if not follow:
            return False
        await self.db.delete(follow)
        await self.db.flush()
        return True

    async def get_followers(self, user_id: str, page: int = 1, page_size: int = 20):
        uid = uuid.UUID(user_id)
        query = (
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == uid, Follow.status == FollowStatus.ACTIVE)
        )
        count_query = (
            select(func.count())
            .select_from(Follow)
            .where(Follow.following_id == uid, Follow.status == FollowStatus.ACTIVE)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_following(self, user_id: str, page: int = 1, page_size: int = 20):
        uid = uuid.UUID(user_id)
        query = (
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == uid, Follow.status == FollowStatus.ACTIVE)
        )
        count_query = (
            select(func.count())
            .select_from(Follow)
            .where(Follow.follower_id == uid, Follow.status == FollowStatus.ACTIVE)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_pending_follow_requests(self, user_id: str, page: int = 1, page_size: int = 20):
        uid = uuid.UUID(user_id)
        query = (
            select(Follow)
            .where(Follow.following_id == uid, Follow.status == FollowStatus.PENDING)
            .order_by(Follow.created_at.desc())
        )
        count_query = (
            select(func.count())
            .select_from(Follow)
            .where(Follow.following_id == uid, Follow.status == FollowStatus.PENDING)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def block_user(self, blocker_id: str, blocked_id: str) -> Optional[Block]:
        if blocker_id == blocked_id:
            return None
        bid = uuid.UUID(blocker_id)
        tid = uuid.UUID(blocked_id)

        existing = await self.db.execute(
            select(Block).where(Block.blocker_id == bid, Block.blocked_id == tid)
        )
        if existing.scalar_one_or_none():
            return None

        block = Block(blocker_id=bid, blocked_id=tid)
        self.db.add(block)

        # Remove existing follows in both directions
        await self.unfollow_user(blocker_id, blocked_id)
        await self.unfollow_user(blocked_id, blocker_id)

        await self.db.flush()
        return block

    async def unblock_user(self, blocker_id: str, blocked_id: str) -> bool:
        bid = uuid.UUID(blocker_id)
        tid = uuid.UUID(blocked_id)
        result = await self.db.execute(
            select(Block).where(Block.blocker_id == bid, Block.blocked_id == tid)
        )
        block = result.scalar_one_or_none()
        if not block:
            return False
        await self.db.delete(block)
        await self.db.flush()
        return True

    async def get_blocked_users(self, user_id: str, page: int = 1, page_size: int = 20):
        uid = uuid.UUID(user_id)
        query = (
            select(User)
            .join(Block, Block.blocked_id == User.id)
            .where(Block.blocker_id == uid)
        )
        count_query = (
            select(func.count())
            .select_from(Block)
            .where(Block.blocker_id == uid)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def is_following(self, follower_id: str, following_id: str) -> bool:
        fid = uuid.UUID(follower_id)
        tid = uuid.UUID(following_id)
        result = await self.db.execute(
            select(Follow).where(
                Follow.follower_id == fid,
                Follow.following_id == tid,
                Follow.status == FollowStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none() is not None

    async def is_blocked(self, user_id: str, target_id: str) -> bool:
        uid = uuid.UUID(user_id)
        tid = uuid.UUID(target_id)
        result = await self.db.execute(
            select(Block).where(
                or_(
                    (Block.blocker_id == uid) & (Block.blocked_id == tid),
                    (Block.blocker_id == tid) & (Block.blocked_id == uid),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_users(self, page: int = 1, page_size: int = 20, search: Optional[str] = None, role: Optional[str] = None):
        query = select(User)
        count_query = select(func.count()).select_from(User)

        if role:
            query = query.where(User.role == UserRole(role))
            count_query = count_query.where(User.role == UserRole(role))
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.display_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def ban_user(self, user_id: str) -> Optional[User]:
        return await self.update_profile(user_id, is_banned=True, is_active=False)

    async def unban_user(self, user_id: str) -> Optional[User]:
        return await self.update_profile(user_id, is_banned=False, is_active=True)
