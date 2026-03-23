"""Poll API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.post import PollVoteRequest
from app.services.post_service import PostService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


@router.post("/{post_id}/vote")
async def vote_poll(
    post_id: str,
    data: PollVoteRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    success = await service.vote_poll(current_user["user_id"], post_id, data.option_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot vote: poll not found, already voted, or poll expired",
        )
    return {"message": "Vote recorded successfully"}


@router.get("/{post_id}/results")
async def get_poll_results(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = PostService(db)
    post = await service.get_by_id(post_id)
    if not post or not post.poll:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")

    poll = post.poll
    return {
        "id": str(poll.id),
        "total_votes": poll.total_votes,
        "expires_at": poll.expires_at.isoformat() if poll.expires_at else None,
        "options": [
            {
                "id": str(o.id),
                "text": o.text,
                "vote_count": o.vote_count,
                "percentage": round((o.vote_count / poll.total_votes * 100) if poll.total_votes > 0 else 0, 1),
            }
            for o in (poll.options or [])
        ],
    }
