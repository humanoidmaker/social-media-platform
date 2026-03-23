"""Message service for direct messaging."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.message import Message, MessageType


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self,
        creator_id: str,
        participant_ids: list[str],
        name: Optional[str] = None,
        is_group: bool = False,
    ) -> Conversation:
        all_ids = list(set([creator_id] + participant_ids))

        # For 1-on-1 conversations, check if one already exists
        if not is_group and len(all_ids) == 2:
            existing = await self._find_direct_conversation(all_ids[0], all_ids[1])
            if existing:
                return existing

        conversation = Conversation(name=name, is_group=is_group)
        self.db.add(conversation)
        await self.db.flush()

        for uid in all_ids:
            participant = ConversationParticipant(
                conversation_id=conversation.id,
                user_id=uuid.UUID(uid),
                is_admin=uid == creator_id,
            )
            self.db.add(participant)

        await self.db.flush()
        return conversation

    async def _find_direct_conversation(self, user_a: str, user_b: str) -> Optional[Conversation]:
        """Find an existing 1-on-1 conversation between two users."""
        ua = uuid.UUID(user_a)
        ub = uuid.UUID(user_b)

        # Find conversations where both users participate and it's not a group
        subquery_a = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == ua)
        )
        subquery_b = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == ub)
        )

        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id.in_(subquery_a),
                Conversation.id.in_(subquery_b),
                Conversation.is_group == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        cid = uuid.UUID(conversation_id)
        result = await self.db.execute(select(Conversation).where(Conversation.id == cid))
        return result.scalar_one_or_none()

    async def get_user_conversations(self, user_id: str, page: int = 1, page_size: int = 20):
        uid = uuid.UUID(user_id)
        subquery = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.user_id == uid)
        )
        query = (
            select(Conversation)
            .where(Conversation.id.in_(subquery))
            .order_by(Conversation.last_message_at.desc().nullslast())
        )
        count_query = (
            select(func.count())
            .select_from(ConversationParticipant)
            .where(ConversationParticipant.user_id == uid)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def is_participant(self, conversation_id: str, user_id: str) -> bool:
        cid = uuid.UUID(conversation_id)
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == cid,
                ConversationParticipant.user_id == uid,
            )
        )
        return result.scalar_one_or_none() is not None

    async def send_message(
        self,
        conversation_id: str,
        sender_id: str,
        content: Optional[str] = None,
        message_type: str = "text",
        media_url: Optional[str] = None,
        media_key: Optional[str] = None,
        shared_post_id: Optional[str] = None,
    ) -> Message:
        cid = uuid.UUID(conversation_id)
        sid = uuid.UUID(sender_id)
        spid = uuid.UUID(shared_post_id) if shared_post_id else None

        message = Message(
            conversation_id=cid,
            sender_id=sid,
            content=content,
            message_type=MessageType(message_type),
            media_url=media_url,
            media_key=media_key,
            shared_post_id=spid,
        )
        self.db.add(message)

        # Update conversation last message
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.last_message_text = content or f"[{message_type}]"
            conversation.last_message_at = datetime.now(timezone.utc)

        await self.db.flush()
        return message

    async def get_messages(self, conversation_id: str, page: int = 1, page_size: int = 50):
        cid = uuid.UUID(conversation_id)
        query = (
            select(Message)
            .where(Message.conversation_id == cid, Message.is_deleted == False)
            .order_by(Message.created_at.desc())
        )
        count_query = (
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == cid, Message.is_deleted == False)
        )
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def mark_as_read(self, conversation_id: str, user_id: str) -> int:
        """Mark all messages in a conversation as read for a user. Returns count updated."""
        cid = uuid.UUID(conversation_id)
        uid = uuid.UUID(user_id)

        result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == cid,
                Message.sender_id != uid,
                Message.is_read == False,
            )
        )
        messages = result.scalars().all()
        for msg in messages:
            msg.is_read = True

        # Update participant's last_read_at
        participant_result = await self.db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == cid,
                ConversationParticipant.user_id == uid,
            )
        )
        participant = participant_result.scalar_one_or_none()
        if participant:
            participant.last_read_at = datetime.now(timezone.utc)

        await self.db.flush()
        return len(messages)

    async def get_unread_count(self, conversation_id: str, user_id: str) -> int:
        cid = uuid.UUID(conversation_id)
        uid = uuid.UUID(user_id)
        result = await self.db.execute(
            select(func.count())
            .select_from(Message)
            .where(
                Message.conversation_id == cid,
                Message.sender_id != uid,
                Message.is_read == False,
            )
        )
        return result.scalar() or 0

    async def delete_message(self, message_id: str, user_id: str) -> bool:
        mid = uuid.UUID(message_id)
        result = await self.db.execute(select(Message).where(Message.id == mid))
        message = result.scalar_one_or_none()
        if not message or str(message.sender_id) != user_id:
            return False
        message.is_deleted = True
        message.content = None
        await self.db.flush()
        return True
