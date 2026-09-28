from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.endpoint import Endpoint
from app.models.user import User
from app.models.webhook_event import WebhookEvent

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    endpoint_total = db.scalar(select(func.count(Endpoint.id)).where(Endpoint.owner_id == current_user.id)) or 0
    endpoint_active = db.scalar(select(func.count(Endpoint.id)).where(Endpoint.owner_id == current_user.id, Endpoint.is_active.is_(True))) or 0
    event_total = db.scalar(select(func.count(WebhookEvent.id)).join(Endpoint).where(Endpoint.owner_id == current_user.id)) or 0
    counts = {}
    for status in ["RECEIVED", "QUEUED", "DELIVERING", "DELIVERED", "FAILED", "RETRY_SCHEDULED", "DLQ"]:
        counts[status.lower()] = db.scalar(select(func.count(WebhookEvent.id)).join(Endpoint).where(Endpoint.owner_id == current_user.id, WebhookEvent.status == status)) or 0
    recent = list(db.scalars(select(WebhookEvent).join(Endpoint).where(Endpoint.owner_id == current_user.id).order_by(WebhookEvent.received_at.desc()).limit(10)))
    return {
        "endpoints": {"total": endpoint_total, "active": endpoint_active},
        "events": {"total": event_total, **counts},
        "recent_events": [
            {"id": str(e.id), "endpoint_id": str(e.endpoint_id), "event_type": e.event_type or "webhook", "status": e.status, "received_at": e.received_at}
            for e in recent
        ],
    }
