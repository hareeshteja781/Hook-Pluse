from redis import Redis
from app.core.config import settings

STREAM_NAME = "hookpluse:webhook_events"
GROUP_NAME = "hookpluse-delivery"
DLQ_STREAM_NAME = "hookpluse:dead_letter"

def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)

def ensure_group(redis_client: Redis) -> None:
    try:
        redis_client.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise

def enqueue_event(redis_client: Redis, event_id: str) -> str:
    return redis_client.xadd(STREAM_NAME, {"event_id": event_id})

def enqueue_dlq(redis_client: Redis, event_id: str, reason: str) -> str:
    return redis_client.xadd(DLQ_STREAM_NAME, {"event_id": event_id, "reason": reason})
