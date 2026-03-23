"""Aggregate stats model for platform analytics."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AggregateStats(Base):
    __tablename__ = "aggregate_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    stat_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[str] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
