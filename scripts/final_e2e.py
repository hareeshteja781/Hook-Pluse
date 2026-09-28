import hashlib
import hmac
import json
import sys
import time
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import httpx

BASE = "http://127.0.0.1:8000"
email = f"final-{uuid.uuid4().hex[:8]}@example.com"
password = "FinalIntegration123!"
client = httpx.Client(timeout=10)

r = client.post(f"{BASE}/api/v1/auth/register", json={"email": email, "password": password})
assert r.status_code == 201, r.text
token = client.post(f"{BASE}/api/v1/auth/login", data={"username": email, "password": password}).json()["access_token"]
auth = {"Authorization": f"Bearer {token}"}
endpoint = client.post(f"{BASE}/api/v1/endpoints", headers=auth, json={"name":"Final receiver","target_url":"http://host.docker.internal:9000/webhook"})
assert endpoint.status_code == 201, endpoint.text
endpoint_data = endpoint.json()
endpoint_id = endpoint_data["id"]
secret = endpoint_data["signing_secret"]

body = json.dumps({"integration":"phase12","value":42}, separators=(",", ":")).encode()
signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
headers = {"Idempotency-Key":"phase12-final-001", "X-Hook-Signature":signature, "X-Event-Type":"integration.test", "Content-Type":"application/json"}
first = client.post(f"{BASE}/api/v1/webhooks/{endpoint_id}", headers=headers, content=body)
assert first.status_code == 202, first.text
assert first.json()["duplicate"] is False
event_id = first.json()["event_id"]
second = client.post(f"{BASE}/api/v1/webhooks/{endpoint_id}", headers=headers, content=body)
assert second.status_code == 202 and second.json()["duplicate"] is True

status = ""
detail = None
for _ in range(30):
    detail = client.get(f"{BASE}/api/v1/events/{event_id}", headers=auth).json()
    status = detail["status"]
    receiver = client.get("http://127.0.0.1:9000/count").json()
    if status == "DELIVERED" and receiver["count"] >= 1:
        break
    time.sleep(1)

assert status == "DELIVERED", detail
assert receiver["count"] >= 1, receiver
assert json.loads(receiver["last_body"]) == json.loads(body.decode())
assert detail["attempts"][0]["http_status"] == 200
metrics = client.get(f"{BASE}/api/v1/metrics/summary", headers=auth).json()
assert metrics["events"]["delivered"] >= 1

print("FINAL_E2E_OK")
print("event_status=", status)
print("receiver_count=", receiver["count"])
print("duplicate_check=", second.json()["duplicate"])
print("delivery_success_rate=", metrics["delivery"]["success_rate"])
client.close()
