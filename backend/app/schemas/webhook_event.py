import uuid
from datetime import datetime
from pydantic import BaseModel

class WebhookReceiveResponse(BaseModel):
    event_id: uuid.UUID
    duplicate: bool
    status: str
    received_at: datetime
