"""Message and conversation schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserListItem


class ConversationParticipantResponse(BaseModel):
    user: UserListItem
    is_admin: bool = False
    last_read_at: Optional[datetime] = None


class ConversationResponse(BaseModel):
    id: str
    name: Optional[str] = None
    is_group: bool = False
    participants: List[ConversationParticipantResponse] = []
    last_message_text: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    created_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender: UserListItem
    message_type: str
    content: Optional[str] = None
    media_url: Optional[str] = None
    shared_post_id: Optional[str] = None
    is_read: bool = False
    created_at: Optional[datetime] = None


class CreateConversationRequest(BaseModel):
    participant_ids: List[str] = Field(min_length=1)
    name: Optional[str] = Field(None, max_length=200)
    is_group: bool = False


class SendMessageRequest(BaseModel):
    content: Optional[str] = Field(None, max_length=5000)
    message_type: str = Field(default="text", pattern=r"^(text|image|video|post_share|story_reply)$")
    shared_post_id: Optional[str] = None


class WebSocketMessage(BaseModel):
    type: str
    conversation_id: Optional[str] = None
    content: Optional[str] = None
    message_id: Optional[str] = None
