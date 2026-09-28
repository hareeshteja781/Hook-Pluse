import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel

class EventAttemptRead(BaseModel):
    id: uuid.UUID
    attempt_number: int
    http_status: int | None
    duration_ms: int | None
    response_body: str | None
    error: str | None
    created_at: datetime

class EventDetail(BaseModel):
    id: uuid.UUID
    endpoint_id: uuid.UUID
    idempotency_key: str
    body_hash: str
    payload: dict[str, Any]
    headers: dict[str, Any]
    signature: str
    event_type: str | None
    status: str
    next_retry_at: datetime | None
    replay_of_id: uuid.UUID | None
    received_at: datetime
    attempts: list[EventAttemptRead]

class ReplayResponse(BaseModel):
    event_id: uuid.UUID
    replay_of_id: uuid.UUID
    status: str
