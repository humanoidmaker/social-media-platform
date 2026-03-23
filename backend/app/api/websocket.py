"""WebSocket routes for real-time messaging and notifications."""

import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.utils.tokens import decode_access_token

router = APIRouter()
logger = logging.getLogger("social_media.websocket")

# In-memory connection store; in production, use Redis pub/sub
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections per user."""

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in active_connections:
            active_connections[user_id] = set()
        active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected: user={user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in active_connections:
            active_connections[user_id].discard(websocket)
            if not active_connections[user_id]:
                del active_connections[user_id]
        logger.info(f"WebSocket disconnected: user={user_id}")

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in active_connections:
            dead = set()
            for ws in active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                active_connections[user_id].discard(ws)

    async def broadcast_to_conversation(self, participant_ids: list[str], message: dict):
        for uid in participant_ids:
            await self.send_to_user(uid, message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """WebSocket endpoint for real-time messaging.

    Connect with: ws://host/ws?token=<jwt_token>

    Message types:
    - {"type": "message", "conversation_id": "...", "content": "..."}
    - {"type": "typing", "conversation_id": "..."}
    - {"type": "read", "conversation_id": "..."}
    - {"type": "ping"}
    """
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["user_id"]
    await manager.connect(websocket, user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "message":
                conversation_id = data.get("conversation_id")
                content = data.get("content")
                if not conversation_id or not content:
                    await websocket.send_json({"type": "error", "message": "Missing conversation_id or content"})
                    continue

                # In production, save message via service and then broadcast
                outgoing = {
                    "type": "new_message",
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "content": content,
                }
                # Broadcast to all connected participants
                # For now, just echo back confirmation
                await websocket.send_json({"type": "message_sent", "conversation_id": conversation_id})

            elif msg_type == "typing":
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    # Broadcast typing indicator (would need participant lookup in production)
                    pass

            elif msg_type == "read":
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    await websocket.send_json({"type": "read_confirmed", "conversation_id": conversation_id})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)
