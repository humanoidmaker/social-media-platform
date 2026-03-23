"""Report API routes (user-facing)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.moderation_service import ModerationService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


class CreateReportRequest(BaseModel):
    target_type: str = Field(pattern=r"^(user|post|comment|message)$")
    target_id: str
    reason: str = Field(
        pattern=r"^(spam|harassment|hate_speech|nudity|violence|misinformation|self_harm|impersonation|intellectual_property|other)$"
    )
    description: Optional[str] = Field(None, max_length=1000)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_report(
    data: CreateReportRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ModerationService(db)
    report = await service.create_report(
        reporter_id=current_user["user_id"],
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
        description=data.description,
    )
    return {
        "id": str(report.id),
        "status": report.status.value,
        "message": "Report submitted. Our team will review it shortly.",
    }
