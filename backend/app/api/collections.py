"""Collections API routes for organizing bookmarks."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.collection import Collection
from app.models.bookmark import Bookmark
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


class CreateCollectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: bool = True


class UpdateCollectionRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: Optional[bool] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CreateCollectionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    collection = Collection(
        user_id=uuid.UUID(current_user["user_id"]),
        name=data.name,
        description=data.description,
        is_private=data.is_private,
    )
    db.add(collection)
    await db.flush()
    return {
        "id": str(collection.id),
        "name": collection.name,
        "description": collection.description,
        "is_private": collection.is_private,
        "created_at": collection.created_at.isoformat() if collection.created_at else None,
    }


@router.get("/")
async def get_collections(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = uuid.UUID(current_user["user_id"])
    query = select(Collection).where(Collection.user_id == uid).order_by(Collection.created_at.desc())
    count_query = select(func.count()).select_from(Collection).where(Collection.user_id == uid)
    total = (await db.execute(count_query)).scalar() or 0
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    collections = result.scalars().all()

    items = []
    for c in collections:
        bookmark_count = (
            await db.execute(
                select(func.count()).select_from(Bookmark).where(Bookmark.collection_id == c.id)
            )
        ).scalar() or 0
        items.append({
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "cover_url": c.cover_url,
            "is_private": c.is_private,
            "bookmark_count": bookmark_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{collection_id}")
async def get_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = uuid.UUID(collection_id)
    result = await db.execute(select(Collection).where(Collection.id == cid))
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    if collection.is_private and str(collection.user_id) != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Collection is private")
    return {
        "id": str(collection.id),
        "name": collection.name,
        "description": collection.description,
        "cover_url": collection.cover_url,
        "is_private": collection.is_private,
        "created_at": collection.created_at.isoformat() if collection.created_at else None,
    }


@router.patch("/{collection_id}")
async def update_collection(
    collection_id: str,
    data: UpdateCollectionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = uuid.UUID(collection_id)
    result = await db.execute(select(Collection).where(Collection.id == cid))
    collection = result.scalar_one_or_none()
    if not collection or str(collection.user_id) != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(collection, key, value)
    await db.flush()
    return {
        "id": str(collection.id),
        "name": collection.name,
        "description": collection.description,
        "is_private": collection.is_private,
    }


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = uuid.UUID(collection_id)
    result = await db.execute(select(Collection).where(Collection.id == cid))
    collection = result.scalar_one_or_none()
    if not collection or str(collection.user_id) != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    await db.delete(collection)
    await db.flush()
    return {"message": "Collection deleted successfully"}
