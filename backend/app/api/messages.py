"""Messages/DM API routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.message import CreateConversationRequest, SendMessageRequest
from app.services.message_service import MessageService
from app.services.user_service import UserService
from app.services.media_service import MediaService
from app.middleware.auth_middleware import get_current_user

router = APIRouter()


def _conversation_to_response(conv, unread: int = 0) -> dict:
    participants = []
    if conv.participants:
        for p in conv.participants:
            participants.append({
                "user_id": str(p.user_id),
                "is_admin": p.is_admin,
                "last_read_at": p.last_read_at.isoformat() if p.last_read_at else None,
            })
    return {
        "id": str(conv.id),
        "name": conv.name,
        "is_group": conv.is_group,
        "participants": participants,
        "last_message_text": conv.last_message_text,
        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
        "unread_count": unread,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    conversation = await service.create_conversation(
        creator_id=current_user["user_id"],
        participant_ids=data.participant_ids,
        name=data.name,
        is_group=data.is_group,
    )
    return _conversation_to_response(conversation)


@router.get("/conversations")
async def get_conversations(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    conversations, total = await service.get_user_conversations(current_user["user_id"], page, page_size)
    items = []
    for conv in conversations:
        unread = await service.get_unread_count(str(conv.id), current_user["user_id"])
        items.append(_conversation_to_response(conv, unread))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    if not await service.is_participant(conversation_id, current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")
    conv = await service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    unread = await service.get_unread_count(conversation_id, current_user["user_id"])
    return _conversation_to_response(conv, unread)


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    data: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    if not await service.is_participant(conversation_id, current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    message = await service.send_message(
        conversation_id=conversation_id,
        sender_id=current_user["user_id"],
        content=data.content,
        message_type=data.message_type,
        shared_post_id=data.shared_post_id,
    )
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "sender_id": str(message.sender_id),
        "message_type": message.message_type.value,
        "content": message.content,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    page: int = 1,
    page_size: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    if not await service.is_participant(conversation_id, current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    messages, total = await service.get_messages(conversation_id, page, page_size)
    return {
        "items": [
            {
                "id": str(m.id),
                "sender_id": str(m.sender_id),
                "message_type": m.message_type.value,
                "content": m.content,
                "media_url": m.media_url,
                "shared_post_id": str(m.shared_post_id) if m.shared_post_id else None,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/conversations/{conversation_id}/read")
async def mark_as_read(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    if not await service.is_participant(conversation_id, current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")
    count = await service.mark_as_read(conversation_id, current_user["user_id"])
    return {"marked_read": count}


@router.post("/conversations/{conversation_id}/media", status_code=status.HTTP_201_CREATED)
async def send_media_message(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    if not await service.is_participant(conversation_id, current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")

    data = await file.read()
    content_type = file.content_type or "application/octet-stream"

    if content_type.startswith("image/"):
        error = MediaService.validate_image(content_type, len(data))
        msg_type = "image"
    elif content_type.startswith("video/"):
        error = MediaService.validate_video(content_type, len(data))
        msg_type = "video"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported media type")

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    extension = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
    key, url = MediaService.upload_message_media(data, content_type, extension)

    message = await service.send_message(
        conversation_id=conversation_id,
        sender_id=current_user["user_id"],
        message_type=msg_type,
        media_url=url,
        media_key=key,
    )
    return {
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "sender_id": str(message.sender_id),
        "message_type": message.message_type.value,
        "media_url": url,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MessageService(db)
    success = await service.delete_message(message_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or not authorized")
    return {"message": "Message deleted"}
