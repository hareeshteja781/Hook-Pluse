import json
import uuid
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.endpoint import Endpoint
from app.models.user import User
from app.models.webhook_event import WebhookEvent
from app.schemas.simulator import SimulatorRequest, SimulatorResponse
from app.services.realtime import publish_event_update
from app.core.config import settings
from redis import Redis
from app.services.webhook_security import body_sha256, generate_signature

router = APIRouter(prefix="/simulator", tags=["simulator"])

@router.post("/send", response_model=SimulatorResponse, status_code=201)
def simulate(payload: SimulatorRequest, db: Annotated[Session, Depends(get_db)], current_user: Annotated[User, Depends(get_current_user)]) -> SimulatorResponse:
    endpoint = db.query(Endpoint).filter(Endpoint.id == payload.endpoint_id, Endpoint.owner_id == current_user.id, Endpoint.is_active.is_(True)).first()
    if not endpoint: raise HTTPException(status_code=404, detail="Endpoint not found")
    created = 0
    for index in range(payload.count):
        event_payload = {"source":"hook-pluse-simulator", "sequence":index + 1, "generated_at":datetime.now(timezone.utc).isoformat()}
        raw = json.dumps(event_payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        event = WebhookEvent(endpoint_id=endpoint.id, idempotency_key=f"sim:{uuid.uuid4()}", body_hash=body_sha256(raw), payload=event_payload, headers={"content-type":"application/json","user-agent":"hook-pluse-simulator"}, signature=generate_signature(raw, endpoint.signing_secret), event_type=payload.event_type, status="RECEIVED")
        db.add(event)
        db.flush()
        publish_event_update(str(event.id), str(current_user.id), event.status, event.event_type)
        created += 1
    db.commit()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    queued_ids = list(db.scalars(select(WebhookEvent.id).where(WebhookEvent.endpoint_id == endpoint.id, WebhookEvent.status == "RECEIVED").order_by(WebhookEvent.received_at.desc()).limit(payload.count)))
    for event_id in queued_ids:
        redis.xadd("hookpluse:webhook_events", {"event_id": str(event_id)})
    if queued_ids:
        db.query(WebhookEvent).filter(WebhookEvent.id.in_(queued_ids)).update({"status": "QUEUED"}, synchronize_session=False)
        db.commit()
    redis.close()
    return SimulatorResponse(created=created, dispatched=len(queued_ids))
