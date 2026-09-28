import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User
from app.services.realtime import REALTIME_CHANNEL

email = f"ws-test-{uuid.uuid4().hex[:8]}@example.com"
password = "WebSocketTest123!"
client = TestClient(app)
r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
assert r.status_code == 201, r.text
token = client.post("/api/v1/auth/login", data={"username": email, "password": password}).json()["access_token"]
me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
user_id = me["id"]
redis = Redis.from_url(settings.redis_url, decode_responses=True)
with client.websocket_connect("/api/v1/ws/events") as ws:
    ws.send_json({"token": token})
    assert ws.receive_json()["type"] == "connected"
    redis.publish(REALTIME_CHANNEL, '{"event_id":"wrong","owner_id":"not-this-user","status":"DELIVERED","event_type":"x"}')
    redis.publish(REALTIME_CHANNEL, f'{{"event_id":"right","owner_id":"{user_id}","status":"DELIVERED","event_type":"invoice.created"}}')
    message = ws.receive_json()
    assert message["type"] == "event_update"
    assert message["data"]["event_id"] == "right"
db = SessionLocal()
try:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        db.delete(user)
        db.commit()
finally:
    db.close()
print("WEBSOCKET_FILTER_TEST_OK")
