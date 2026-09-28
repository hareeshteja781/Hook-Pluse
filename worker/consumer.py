import socket
import time
from redis import Redis
from worker.stream import GROUP_NAME, STREAM_NAME, ensure_group, get_redis
from worker.delivery import deliver_event

def consume_once(redis_client: Redis, consumer_name: str) -> int:
    messages = redis_client.xreadgroup(GROUP_NAME, consumer_name, {STREAM_NAME: ">"}, count=10, block=1000)
    processed = 0
    for _, entries in messages:
        for message_id, data in entries:
            try:
                event_id = data.get("event_id")
                if event_id:
                    deliver_event(event_id)
            except Exception:
                continue
            redis_client.xack(STREAM_NAME, GROUP_NAME, message_id)
            processed += 1
    return processed

def consume_loop() -> None:
    redis_client = get_redis()
    ensure_group(redis_client)
    consumer_name = f"worker-{socket.gethostname()}"
    while True:
        consume_once(redis_client, consumer_name)
        time.sleep(0.1)
