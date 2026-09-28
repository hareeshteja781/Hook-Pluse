import asyncio
import json
import uuid
import httpx
import websockets
from redis import Redis

BASE="http://127.0.0.1:8000"
email=f"container-ws-{uuid.uuid4().hex[:8]}@example.com"
password="ContainerWebSocket123!"

def get_token():
    with httpx.Client(timeout=10) as client:
        r=client.post(f"{BASE}/api/v1/auth/register",json={"email":email,"password":password})
        assert r.status_code==201,r.text
        r=client.post(f"{BASE}/api/v1/auth/login",data={"username":email,"password":password})
        assert r.status_code==200,r.text
        token=r.json()["access_token"]
        user=client.get(f"{BASE}/api/v1/auth/me",headers={"Authorization":f"Bearer {token}"}).json()
        return token,user["id"]

async def main():
    token,user_id=get_token()
    async with websockets.connect(f"ws://127.0.0.1:8000/api/v1/ws/events") as ws:
        await ws.send(json.dumps({"token":token}))
        connected=json.loads(await ws.recv())
        assert connected["type"]=="connected"
        Redis.from_url("redis://127.0.0.1:6379/0",decode_responses=True).publish("hookpluse:realtime",json.dumps({"event_id":"container-ws","owner_id":user_id,"status":"DELIVERED","event_type":"container.test"}))
        message=json.loads(await ws.recv())
        assert message["type"]=="event_update" and message["data"]["event_id"]=="container-ws"
    print("CONTAINER_WEBSOCKET_OK")
    print("TEST_EMAIL",email)

asyncio.run(main())
