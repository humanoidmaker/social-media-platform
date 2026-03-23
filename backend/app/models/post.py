"""Post model."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PostType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    REPOST = "repost"
    POLL = "poll"


class PostVisibility(str, enum.Enum):
    PUBLIC = "public"
    FOLLOWERS = "followers"
    CLOSE_FRIENDS = "close_friends"
    PRIVATE = "private"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    post_type: Mapped[PostType] = mapped_column(Enum(PostType), default=PostType.TEXT, nullable=False)
    visibility: Mapped[PostVisibility] = mapped_column(
        Enum(PostVisibility), default=PostVisibility.PUBLIC, nullable=False
    )
    repost_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="SET NULL"), nullable=True
    )
    quote_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    repost_count: Mapped[int] = mapped_column(Integer, default=0)
    bookmark_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_comments_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="posts", lazy="selectin")  # noqa: F821
    media: Mapped[list["PostMedia"]] = relationship("PostMedia", back_populates="post", lazy="selectin", cascade="all, delete-orphan")  # noqa: F821
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="post", lazy="selectin", cascade="all, delete-orphan")  # noqa: F821
    likes: Mapped[list["Like"]] = relationship("Like", back_populates="post", lazy="selectin", cascade="all, delete-orphan")  # noqa: F821
    poll: Mapped[Optional["Poll"]] = relationship("Poll", back_populates="post", uselist=False, lazy="selectin", cascade="all, delete-orphan")  # noqa: F821
    original_post: Mapped[Optional["Post"]] = relationship("Post", remote_side="Post.id", lazy="selectin")
