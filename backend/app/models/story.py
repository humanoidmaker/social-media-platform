"""Story model."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StoryMediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_type: Mapped[StoryMediaType] = mapped_column(Enum(StoryMediaType), nullable=False)
    media_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    media_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=5)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    is_close_friends: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    author: Mapped["User"] = relationship("User", back_populates="stories")  # noqa: F821
    views: Mapped[list["StoryView"]] = relationship("StoryView", back_populates="story", lazy="selectin", cascade="all, delete-orphan")  # noqa: F821
