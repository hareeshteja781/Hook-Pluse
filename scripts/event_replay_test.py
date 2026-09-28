import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.endpoint import Endpoint
from app.models.user import User
from app.models.webhook_event import WebhookEvent

client = TestClient(app)
email = f"replay-test-{uuid.uuid4().hex[:8]}@example.com"
password = "ReplayTest123!"
other_email = f"other-{uuid.uuid4().hex[:8]}@example.com"
r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
assert r.status_code == 201, r.text
token = client.post("/api/v1/auth/login", data={"username": email, "password": password}).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
owner = client.get("/api/v1/auth/me", headers=headers).json()
db = SessionLocal()
try:
    endpoint = Endpoint(owner_id=owner["id"], name="Replay Test", target_url="https://example.com/hook", signing_secret="test-secret")
    db.add(endpoint); db.flush()
    event = WebhookEvent(endpoint_id=endpoint.id, idempotency_key="original-1", body_hash="a" * 64, payload={"hello":"world"}, headers={"content-type":"application/json"}, signature="sha256:test", event_type="demo.created", status="DELIVERED")
    db.add(event); db.commit(); db.refresh(event); event_id = str(event.id)
    db.add(User(email=other_email, hashed_password=hash_password(password))); db.commit()
finally: db.close()

detail = client.get(f"/api/v1/events/{event_id}", headers=headers)
assert detail.status_code == 200, detail.text
assert detail.json()["payload"]["hello"] == "world"
replay = client.post(f"/api/v1/events/{event_id}/replay", headers=headers)
assert replay.status_code == 201, replay.text
assert replay.json()["replay_of_id"] == event_id

other_token = client.post("/api/v1/auth/login", data={"username": other_email, "password": password}).json()["access_token"]
other = client.get(f"/api/v1/events/{event_id}", headers={"Authorization": f"Bearer {other_token}"})
assert other.status_code == 404

db = SessionLocal()
try:
    user = db.scalar(select(User).where(User.email == email))
    other_user = db.scalar(select(User).where(User.email == other_email))
    if user: db.delete(user)
    if other_user: db.delete(other_user)
    db.commit()
finally: db.close()
print("EVENT_INSPECTOR_REPLAY_OK")
