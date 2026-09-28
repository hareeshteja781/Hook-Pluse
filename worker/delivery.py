import json
import time
import uuid
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.delivery_attempt import DeliveryAttempt
from app.models.endpoint import Endpoint
from app.models.webhook_event import WebhookEvent
from app.services.realtime import publish_event_update
from app.services.webhook_security import generate_signature
from worker.stream import enqueue_dlq, get_redis

HTTP_TIMEOUT = 10.0

def retry_delay_seconds(attempt_number: int) -> int:
    return settings.retry_base_seconds * (2 ** (attempt_number - 1))

def determine_delivery_status(attempt_number: int, success: bool) -> str:
    if success:
        return "DELIVERED"
    return "DLQ" if attempt_number >= settings.max_delivery_attempts else "RETRY_SCHEDULED"

def claim_event(event_id: str) -> tuple[uuid.UUID, Endpoint] | None:
    db: Session = SessionLocal()
    try:
        event = db.scalar(select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update())
        if not event or event.status != "QUEUED":
            return None
        endpoint = db.scalar(select(Endpoint).where(Endpoint.id == event.endpoint_id))
        if not endpoint or not endpoint.is_active:
            event.status = "FAILED"
            db.commit()
            if endpoint:
                publish_event_update(str(event.id), str(endpoint.owner_id), event.status, event.event_type)
            return None
        event.status = "DELIVERING"
        db.commit()
        publish_event_update(str(event.id), str(endpoint.owner_id), event.status, event.event_type)
        return event.id, endpoint
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def next_attempt_number(event_id: uuid.UUID) -> int:
    db: Session = SessionLocal()
    try:
        current = db.scalar(select(func.max(DeliveryAttempt.attempt_number)).where(DeliveryAttempt.event_id == event_id))
        return (current or 0) + 1
    finally:
        db.close()

def record_attempt(event_id: uuid.UUID, attempt_number: int, http_status: int | None, duration_ms: int, response_body: str | None, error: str | None, success: bool) -> str:
    retry_at = None
    final_status = "DELIVERED"
    if not success:
        if attempt_number >= settings.max_delivery_attempts:
            final_status = "DLQ"
        else:
            retry_at = datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds(attempt_number))
            final_status = "RETRY_SCHEDULED"

    db: Session = SessionLocal()
    try:
        event = db.scalar(select(WebhookEvent).where(WebhookEvent.id == event_id).with_for_update())
        if not event:
            return final_status
        db.add(DeliveryAttempt(event_id=event_id, attempt_number=attempt_number, http_status=http_status, duration_ms=duration_ms, response_body=response_body, error=error))
        event.status = final_status
        event.next_retry_at = retry_at
        db.commit()
        owner_id = db.scalar(select(Endpoint.owner_id).where(Endpoint.id == event.endpoint_id))
        if owner_id:
            publish_event_update(str(event.id), str(owner_id), final_status, event.event_type)
        return final_status
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def deliver_event(event_id: str) -> None:
    claimed = claim_event(event_id)
    if not claimed:
        return
    event_uuid, endpoint = claimed
    db: Session = SessionLocal()
    try:
        event = db.get(WebhookEvent, event_uuid)
        if not event:
            return
        payload = event.payload
    finally:
        db.close()

    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Hook-Event-ID": str(event_uuid),
        "X-Hook-Event-Type": event.event_type or "webhook",
        "X-Hook-Signature": generate_signature(body, endpoint.signing_secret),
        "X-Hook-Delivery": str(uuid.uuid4()),
    }
    attempt_number = next_attempt_number(event_uuid)
    started = time.perf_counter()
    status_code: int | None = None
    response_body: str | None = None
    error: str | None = None
    success = False
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.post(endpoint.target_url, content=body, headers=headers)
        status_code = response.status_code
        response_body = response.text[:4000]
        success = 200 <= status_code < 300
    except httpx.HTTPError as exc:
        error = str(exc)[:4000]
    duration_ms = int((time.perf_counter() - started) * 1000)
    final_status = record_attempt(
        event_uuid, attempt_number, status_code, duration_ms, response_body, error, success
    )
    if final_status == "DLQ":
        enqueue_dlq(get_redis(), str(event_uuid), error or f"HTTP {status_code}")
