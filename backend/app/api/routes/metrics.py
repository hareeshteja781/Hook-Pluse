from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.delivery_attempt import DeliveryAttempt
from app.models.endpoint import Endpoint
from app.models.user import User
from app.models.webhook_event import WebhookEvent

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/summary")
def metrics_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    owner_filter = Endpoint.owner_id == current_user.id
    event_query = select(func.count(WebhookEvent.id)).join(Endpoint).where(owner_filter)
    event_total = db.scalar(event_query) or 0
    delivered = db.scalar(select(func.count(WebhookEvent.id)).join(Endpoint).where(owner_filter, WebhookEvent.status == "DELIVERED")) or 0
    failed = db.scalar(select(func.count(WebhookEvent.id)).join(Endpoint).where(owner_filter, WebhookEvent.status == "FAILED")) or 0
    dlq = db.scalar(select(func.count(WebhookEvent.id)).join(Endpoint).where(owner_filter, WebhookEvent.status == "DLQ")) or 0
    attempts = list(db.scalars(
        select(DeliveryAttempt).join(WebhookEvent, DeliveryAttempt.event_id == WebhookEvent.id).join(Endpoint, Endpoint.id == WebhookEvent.endpoint_id).where(owner_filter)
    ))
    successful_attempts = sum(1 for a in attempts if a.http_status is not None and 200 <= a.http_status < 300)
    durations = [a.duration_ms for a in attempts if a.duration_ms is not None]
    avg_latency_ms = round(sum(durations) / len(durations), 2) if durations else 0
    success_rate = round((delivered / event_total) * 100, 2) if event_total else 0
    return {
        "events": {"total": event_total, "delivered": delivered, "failed": failed, "dlq": dlq},
        "delivery": {"attempts": len(attempts), "successful_attempts": successful_attempts, "success_rate": success_rate, "avg_latency_ms": avg_latency_ms},
    }
