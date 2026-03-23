"""Admin analytics API routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.middleware.auth_middleware import require_admin

router = APIRouter()


@router.get("/overview")
async def get_platform_overview(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_platform_overview()


@router.get("/user-growth")
async def get_user_growth(
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    data = await service.get_user_growth(days)
    return {"period": f"{days}_days", "data": data}


@router.get("/content")
async def get_content_analytics(
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_content_analytics(days)


@router.get("/user/{user_id}")
async def get_user_analytics(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_user_analytics(user_id)
