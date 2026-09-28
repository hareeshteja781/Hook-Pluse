import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.delivery_attempt import DeliveryAttempt
from app.models.endpoint import Endpoint
from app.models.user import User
from app.models.webhook_event import WebhookEvent
from app.schemas.event_inspector import EventDetail, EventAttemptRead, ReplayResponse
from app.services.realtime import publish_event_update

router = APIRouter(prefix="/events", tags=["events"])

def _get_owned_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> WebhookEvent | None:
    return db.scalar(
        select(WebhookEvent).join(Endpoint, Endpoint.id == WebhookEvent.endpoint_id).where(
            WebhookEvent.id == event_id, Endpoint.owner_id == user_id
        )
    )

@router.get("/{event_id}", response_model=EventDetail)
def get_event(
    event_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EventDetail:
    event = _get_owned_event(db, event_id, current_user.id)
    if not event: raise HTTPException(status_code=404, detail="Event not found")
    attempts = list(db.scalars(
        select(DeliveryAttempt).where(DeliveryAttempt.event_id == event.id).order_by(DeliveryAttempt.attempt_number)
    ))
    return EventDetail(
        id=event.id, endpoint_id=event.endpoint_id, idempotency_key=event.idempotency_key,
        body_hash=event.body_hash, payload=event.payload, headers=event.headers,
        signature=event.signature, event_type=event.event_type, status=event.status,
        next_retry_at=event.next_retry_at, replay_of_id=event.replay_of_id,
        received_at=event.received_at,
        attempts=[EventAttemptRead.model_validate(a, from_attributes=True) for a in attempts],
    )

@router.post("/{event_id}/replay", response_model=ReplayResponse, status_code=status.HTTP_201_CREATED)
def replay_event(
    event_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReplayResponse:
    event = _get_owned_event(db, event_id, current_user.id)
    if not event: raise HTTPException(status_code=404, detail="Event not found")
    replay = WebhookEvent(
        endpoint_id=event.endpoint_id, idempotency_key=f"replay:{uuid.uuid4()}",
        body_hash=event.body_hash, payload=event.payload.copy(), headers={**event.headers, "X-Hook-Replay-Of": str(event.id)},
        signature=f"replay-of:{event.id}", event_type=event.event_type, status="RECEIVED", replay_of_id=event.id
    )
    db.add(replay)
    db.commit()
    db.refresh(replay)
    publish_event_update(str(replay.id), str(current_user.id), replay.status, replay.event_type)
    return ReplayResponse(event_id=replay.id, replay_of_id=event.id, status=replay.status)

