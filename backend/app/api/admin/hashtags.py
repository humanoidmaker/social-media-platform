"""Admin hashtag management API routes."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.hashtag import Hashtag
from app.middleware.auth_middleware import require_admin

router = APIRouter()


@router.get("/")
async def list_hashtags(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(Hashtag)
    count_query = select(func.count()).select_from(Hashtag)

    if search:
        query = query.where(Hashtag.name.ilike(f"%{search}%"))
        count_query = count_query.where(Hashtag.name.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Hashtag.post_count.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    hashtags = result.scalars().all()

    return {
        "items": [
            {"id": str(h.id), "name": h.name, "post_count": h.post_count, "created_at": h.created_at.isoformat() if h.created_at else None}
            for h in hashtags
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.delete("/{hashtag_id}")
async def delete_hashtag(
    hashtag_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    hid = uuid.UUID(hashtag_id)
    result = await db.execute(select(Hashtag).where(Hashtag.id == hid))
    hashtag = result.scalar_one_or_none()
    if not hashtag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hashtag not found")
    await db.delete(hashtag)
    await db.flush()
    return {"message": "Hashtag deleted successfully"}
