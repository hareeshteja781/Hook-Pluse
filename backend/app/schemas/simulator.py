import uuid
from pydantic import BaseModel, Field

class SimulatorRequest(BaseModel):
    endpoint_id: uuid.UUID
    count: int = Field(default=1, ge=1, le=100)
    event_type: str = Field(default="simulator.event", min_length=1, max_length=255)

class SimulatorResponse(BaseModel):
    created: int
    dispatched: int
