"""Admin report management API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.admin import ResolveReportRequest
from app.services.moderation_service import ModerationService
from app.middleware.auth_middleware import require_admin

router = APIRouter()


@router.get("/")
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    report_status: Optional[str] = Query(None, alias="status"),
    target_type: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ModerationService(db)
    reports, total = await service.list_reports(page, page_size, report_status, target_type)
    return {
        "items": [
            {
                "id": str(r.id),
                "reporter_id": str(r.reporter_id),
                "target_type": r.target_type,
                "target_id": str(r.target_id),
                "reason": r.reason.value if hasattr(r.reason, "value") else r.reason,
                "description": r.description,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
                "reviewed_by": str(r.reviewed_by) if r.reviewed_by else None,
                "resolution_note": r.resolution_note,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats")
async def get_report_stats(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ModerationService(db)
    return await service.get_report_stats()


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ModerationService(db)
    report = await service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return {
        "id": str(report.id),
        "reporter_id": str(report.reporter_id),
        "target_type": report.target_type,
        "target_id": str(report.target_id),
        "reason": report.reason.value if hasattr(report.reason, "value") else report.reason,
        "description": report.description,
        "status": report.status.value if hasattr(report.status, "value") else report.status,
        "reviewed_by": str(report.reviewed_by) if report.reviewed_by else None,
        "resolution_note": report.resolution_note,
        "resolved_at": report.resolved_at.isoformat() if report.resolved_at else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


@router.post("/{report_id}/resolve")
async def resolve_report(
    report_id: str,
    data: ResolveReportRequest,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = ModerationService(db)
    report = await service.resolve_report(
        report_id=report_id,
        reviewer_id=current_user["user_id"],
        status=data.status,
        resolution_note=data.resolution_note,
        action=data.action,
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return {"message": f"Report {data.status} successfully", "id": str(report.id)}
