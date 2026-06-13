import uuid
from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None = None
    content: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID | None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
