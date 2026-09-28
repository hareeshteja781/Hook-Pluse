import json
from redis import Redis
from app.core.config import settings

REALTIME_CHANNEL = "hookpluse:realtime"
_redis: Redis | None = None

def get_realtime_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis

def publish_event_update(
    event_id: str, owner_id: str, status: str, event_type: str | None = None
) -> None:
    message = {
        "event_id": event_id,
        "owner_id": owner_id,
        "status": status,
        "event_type": event_type or "webhook",
    }
    get_realtime_redis().publish(REALTIME_CHANNEL, json.dumps(message))
