import time
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.webhook_event import WebhookEvent
from worker.stream import enqueue_event, get_redis

BATCH_SIZE = 50

def dispatch_once() -> int:
    redis_client = get_redis()
    db: Session = SessionLocal()
    count = 0
    try:
        events = list(db.scalars(
            select(WebhookEvent)
            .where(or_(
                WebhookEvent.status == "RECEIVED",
                and_(WebhookEvent.status == "RETRY_SCHEDULED", WebhookEvent.next_retry_at <= func.now()),
            ))
            .order_by(WebhookEvent.received_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
        ))
        for event in events:
            enqueue_event(redis_client, str(event.id))
            event.status = "QUEUED"
            event.next_retry_at = None
            count += 1
        db.commit()
        return count
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def dispatch_loop(stop_seconds: float = 1.0) -> None:
    while True:
        dispatched = dispatch_once()
        if dispatched == 0:
            time.sleep(stop_seconds)
