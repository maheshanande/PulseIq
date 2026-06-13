import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pulseiq_backend.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="messages")  # noqa: F821
    user: Mapped["User"] = relationship(back_populates="messages")  # noqa: F821
    events: Mapped[list["EventSource"]] = relationship(back_populates="message")  # noqa: F821
    embedding: Mapped["MessageEmbedding"] = relationship(back_populates="message", uselist=False)  # noqa: F821
    entity_mentions: Mapped[list["EntityMention"]] = relationship(back_populates="message")  # noqa: F821

    __table_args__ = (Index("ix_messages_tenant_created", "tenant_id", "created_at"),)
