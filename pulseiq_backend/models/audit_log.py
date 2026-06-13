import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from pulseiq_backend.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    query_session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("query_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_message_ids: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    retrieved_event_ids: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    prompt_used: Mapped[str] = mapped_column(Text, nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
