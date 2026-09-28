import uuid
from datetime import datetime
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

class EndpointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    target_url: AnyHttpUrl

class EndpointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    target_url: AnyHttpUrl
    is_active: bool
    created_at: datetime

class EndpointCreated(EndpointRead):
    signing_secret: str
