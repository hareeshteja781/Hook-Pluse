import asyncio
import json
from typing import Annotated
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session
from redis.asyncio import Redis as AsyncRedis
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import decode_access_token
from app.models.user import User
from app.services.realtime import REALTIME_CHANNEL

router = APIRouter(tags=["realtime"])

@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket, db: Annotated[Session, Depends(get_db)]) -> None:
    await websocket.accept()
    try:
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=5)
    except (asyncio.TimeoutError, ValueError):
        await websocket.close(code=4401)
        return
    email = decode_access_token(str(auth_message.get("token", "")))
    user = db.scalar(select(User).where(User.email == email)) if email else None
    if not user or not user.is_active:
        await websocket.close(code=4401)
        return

    redis = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(REALTIME_CHANNEL)
    try:
        await websocket.send_json({"type": "connected"})
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not message:
                continue
            data = json.loads(message["data"])
            if data.get("owner_id") == str(user.id):
                await websocket.send_json({"type": "event_update", "data": data})
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(REALTIME_CHANNEL)
        await pubsub.close()
        await redis.aclose()
