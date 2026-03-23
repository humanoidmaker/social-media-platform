"""Admin dashboard API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.middleware.auth_middleware import require_admin

router = APIRouter()


@router.get("/")
async def get_dashboard(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_admin_dashboard()


@router.get("/overview")
async def get_overview(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_platform_overview()
