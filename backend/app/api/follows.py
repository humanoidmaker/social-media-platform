"""Follow/unfollow API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.user_service import UserService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/{user_id}/follow")
async def follow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    follow = await service.follow_user(current_user["user_id"], user_id)
    if not follow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow this user")
    return {
        "id": str(follow.id),
        "follower_id": str(follow.follower_id),
        "following_id": str(follow.following_id),
        "status": follow.status.value,
        "message": "Follow request sent" if follow.status.value == "pending" else "Followed successfully",
    }


@router.delete("/{user_id}/follow")
async def unfollow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    success = await service.unfollow_user(current_user["user_id"], user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow relationship not found")
    return {"message": "Unfollowed successfully"}


@router.get("/requests")
async def get_follow_requests(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    requests, total = await service.get_pending_follow_requests(current_user["user_id"], page, page_size)
    items = []
    for req in requests:
        follower = await service.get_by_id(str(req.follower_id))
        if follower:
            items.append({
                "id": str(req.id),
                "follower": {
                    "id": str(follower.id),
                    "username": follower.username,
                    "display_name": follower.display_name,
                    "avatar_url": follower.avatar_url,
                    "is_verified": follower.is_verified,
                },
                "created_at": req.created_at.isoformat() if req.created_at else None,
            })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/requests/{follower_id}/accept")
async def accept_follow_request(
    follower_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    success = await service.accept_follow_request(current_user["user_id"], follower_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow request not found")
    return {"message": "Follow request accepted"}


@router.post("/requests/{follower_id}/reject")
async def reject_follow_request(
    follower_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    success = await service.reject_follow_request(current_user["user_id"], follower_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow request not found")
    return {"message": "Follow request rejected"}


@router.get("/{user_id}/status")
async def get_follow_status(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    is_following = await service.is_following(current_user["user_id"], user_id)
    is_followed_by = await service.is_following(user_id, current_user["user_id"])
    is_blocked = await service.is_blocked(current_user["user_id"], user_id)
    return {
        "is_following": is_following,
        "is_followed_by": is_followed_by,
        "is_blocked": is_blocked,
    }
