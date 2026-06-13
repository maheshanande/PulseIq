import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ExtractedEvent(BaseModel):
    """Validated structure expected from LLM JSON output."""
    entity_type: str
    entity_name: str
    aliases: list[str] = Field(default_factory=list)
    event_type: str
    status: str
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractedEntityMention(BaseModel):
    """Raw entity observation extracted from a message."""
    mention_text: str
    entity_type: str
    confidence: float = Field(ge=0.0, le=1.0)


class EventResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    entity_id: uuid.UUID
    event_type: str
    status: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}
