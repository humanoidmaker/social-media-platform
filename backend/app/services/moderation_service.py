"""Moderation service for handling reports and content moderation."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportReason, ReportStatus
from app.models.post import Post
from app.models.user import User


class ModerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self,
        reporter_id: str,
        target_type: str,
        target_id: str,
        reason: str,
        description: Optional[str] = None,
    ) -> Report:
        rid = uuid.UUID(reporter_id)
        tid = uuid.UUID(target_id)
        report = Report(
            reporter_id=rid,
            target_type=target_type,
            target_id=tid,
            reason=ReportReason(reason),
            description=description,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def get_report(self, report_id: str) -> Optional[Report]:
        rid = uuid.UUID(report_id)
        result = await self.db.execute(select(Report).where(Report.id == rid))
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        target_type: Optional[str] = None,
    ):
        query = select(Report)
        count_query = select(func.count()).select_from(Report)

        if status:
            query = query.where(Report.status == ReportStatus(status))
            count_query = count_query.where(Report.status == ReportStatus(status))
        if target_type:
            query = query.where(Report.target_type == target_type)
            count_query = count_query.where(Report.target_type == target_type)

        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.order_by(Report.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def resolve_report(
        self,
        report_id: str,
        reviewer_id: str,
        status: str,
        resolution_note: Optional[str] = None,
        action: Optional[str] = None,
    ) -> Optional[Report]:
        report = await self.get_report(report_id)
        if not report:
            return None

        report.status = ReportStatus(status)
        report.reviewed_by = uuid.UUID(reviewer_id)
        report.resolution_note = resolution_note
        report.resolved_at = datetime.now(timezone.utc)

        # Execute moderation action
        if action == "hide_content" and report.target_type == "post":
            post_result = await self.db.execute(select(Post).where(Post.id == report.target_id))
            post = post_result.scalar_one_or_none()
            if post:
                post.is_hidden = True

        elif action == "ban_user":
            # Find the target user
            if report.target_type == "user":
                user_result = await self.db.execute(select(User).where(User.id == report.target_id))
            elif report.target_type == "post":
                post_result = await self.db.execute(select(Post).where(Post.id == report.target_id))
                post = post_result.scalar_one_or_none()
                if post:
                    user_result = await self.db.execute(select(User).where(User.id == post.author_id))
                else:
                    user_result = None
            else:
                user_result = None

            if user_result:
                user = user_result.scalar_one_or_none()
                if user:
                    user.is_banned = True
                    user.is_active = False

        await self.db.flush()
        return report

    async def get_report_stats(self) -> dict:
        """Get report statistics for the admin dashboard."""
        total = (await self.db.execute(select(func.count()).select_from(Report))).scalar() or 0
        pending = (
            await self.db.execute(
                select(func.count()).select_from(Report).where(Report.status == ReportStatus.PENDING)
            )
        ).scalar() or 0
        resolved = (
            await self.db.execute(
                select(func.count()).select_from(Report).where(Report.status == ReportStatus.RESOLVED)
            )
        ).scalar() or 0
        dismissed = (
            await self.db.execute(
                select(func.count()).select_from(Report).where(Report.status == ReportStatus.DISMISSED)
            )
        ).scalar() or 0

        return {
            "total": total,
            "pending": pending,
            "resolved": resolved,
            "dismissed": dismissed,
        }
