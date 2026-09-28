import json
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.endpoint import Endpoint
from app.models.webhook_event import WebhookEvent
from app.schemas.webhook_event import WebhookReceiveResponse
from app.services.realtime import publish_event_update
from app.services.webhook_security import body_sha256, verify_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/{endpoint_id}", response_model=WebhookReceiveResponse, status_code=status.HTTP_202_ACCEPTED)
async def receive_webhook(
    endpoint_id: UUID, request: Request,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    x_hook_signature: Annotated[str | None, Header(alias="X-Hook-Signature")] = None,
    x_event_type: Annotated[str | None, Header(alias="X-Event-Type")] = None,
) -> WebhookReceiveResponse:
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header is required")
    if not x_hook_signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Hook-Signature header is required")

    db: Session = SessionLocal()
    try:
        endpoint = db.scalar(select(Endpoint).where(Endpoint.id == endpoint_id, Endpoint.is_active.is_(True)))
        if not endpoint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook endpoint not found")
        raw_body = await request.body()
        if not verify_signature(raw_body, x_hook_signature, endpoint.signing_secret):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook body must be valid JSON") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook JSON body must be an object")

        existing = db.scalar(select(WebhookEvent).where(WebhookEvent.endpoint_id == endpoint.id, WebhookEvent.idempotency_key == idempotency_key))
        if existing:
            return WebhookReceiveResponse(event_id=existing.id, duplicate=True, status=existing.status, received_at=existing.received_at)

        event = WebhookEvent(endpoint_id=endpoint.id, idempotency_key=idempotency_key, body_hash=body_sha256(raw_body), payload=payload, headers=dict(request.headers), signature=x_hook_signature, event_type=x_event_type)
        db.add(event)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(WebhookEvent).where(WebhookEvent.endpoint_id == endpoint.id, WebhookEvent.idempotency_key == idempotency_key))
            if not existing:
                raise
            return WebhookReceiveResponse(event_id=existing.id, duplicate=True, status=existing.status, received_at=existing.received_at)
        db.refresh(event)
        publish_event_update(str(event.id), str(endpoint.owner_id), event.status, event.event_type)
        return WebhookReceiveResponse(event_id=event.id, duplicate=False, status=event.status, received_at=event.received_at)
    finally:
        db.close()
