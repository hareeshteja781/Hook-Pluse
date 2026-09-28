import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import select
from app.db.session import SessionLocal
from app.main import app
from app.models.endpoint import Endpoint
from app.models.user import User

client = TestClient(app)
email = f"metric-test-{uuid.uuid4().hex[:8]}@example.com"
password = "MetricTest123!"
assert client.post("/api/v1/auth/register", json={"email": email, "password": password}).status_code == 201
token = client.post("/api/v1/auth/login", data={"username": email, "password": password}).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
owner = client.get("/api/v1/auth/me", headers=headers).json()
db = SessionLocal()
try:
    endpoint = Endpoint(owner_id=owner["id"], name="Metric Test", target_url="https://example.com/webhook", signing_secret="metric-secret")
    db.add(endpoint); db.commit(); db.refresh(endpoint); endpoint_id = str(endpoint.id)
finally: db.close()

r = client.post("/api/v1/simulator/send", json={"endpoint_id": endpoint_id, "count": 3, "event_type": "simulated.created"}, headers=headers)
assert r.status_code == 201, r.text
assert r.json()["created"] == 3
r = client.get("/api/v1/metrics/summary", headers=headers)
assert r.status_code == 200, r.text
metrics = r.json()
assert metrics["events"]["total"] == 3
assert metrics["delivery"]["attempts"] == 0
r = client.get("/api/v1/dashboard/summary", headers=headers)
assert r.status_code == 200
assert r.json()["events"]["total"] == 3

db = SessionLocal()
try:
    user = db.scalar(select(User).where(User.email == email))
    if user: db.delete(user); db.commit()
finally: db.close()
print("METRICS_SIMULATOR_OK", metrics["events"], metrics["delivery"])
