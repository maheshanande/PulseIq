import uuid
from datetime import datetime

from pydantic import BaseModel


class QueryRequest(BaseModel):
    tenant_id: uuid.UUID
    question: str
    user_id: uuid.UUID | None = None


class ConfidenceScore(BaseModel):
    score: float
    label: str  # High / Medium / Low


class TimelineEntry(BaseModel):
    time: str
    event: str
    entity_name: str
    reported_by: str
    source_message_ids: list[uuid.UUID]


class SourceEntry(BaseModel):
    message_id: uuid.UUID
    submitted_by: str
    content: str


class ReasoningBlock(BaseModel):
    messages_analyzed: int
    events_found: int
    entity: str | None


class QueryResponse(BaseModel):
    executive_summary: str
    current_status: str | None
    assessment: str | None
    confidence: ConfidenceScore
    timeline: list[TimelineEntry]
    sources: list[SourceEntry]
    reasoning: ReasoningBlock
