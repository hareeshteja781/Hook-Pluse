import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.main import app

email = f"phase7-test-{uuid.uuid4().hex[:8]}@example.com"
password = "Phase7Test123!"
client = TestClient(app)
r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
assert r.status_code == 201, r.text
r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
assert r.status_code == 200, r.text
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
r = client.post("/api/v1/endpoints", json={"name": "Phase 7 Test", "target_url": "https://example.com/webhook"}, headers=headers)
assert r.status_code == 201, r.text
endpoint_id = r.json()["id"]
r = client.get("/api/v1/endpoints", headers=headers)
assert r.status_code == 200 and any(x["id"] == endpoint_id for x in r.json())
r = client.get("/api/v1/dashboard/summary", headers=headers)
assert r.status_code == 200, r.text
summary = r.json()
assert summary["endpoints"]["total"] >= 1
db = SessionLocal()
try:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        db.delete(user)
        db.commit()
finally:
    db.close()
print("PHASE7_API_E2E_OK", summary["endpoints"], summary["events"]["total"])
