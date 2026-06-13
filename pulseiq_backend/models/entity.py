import uuid

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pulseiq_backend.core.database import Base

ENTITY_TYPES = (
    "customer", "supplier", "vendor", "order", "invoice",
    "payment", "shipment", "machine", "production_line", "deal",
)


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, server_default="{}")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    mentions: Mapped[list["EntityMention"]] = relationship(back_populates="entity")
    alias_rows: Mapped[list["EntityAlias"]] = relationship(back_populates="entity")

    __table_args__ = (Index("ix_entities_tenant_canonical_name", "tenant_id", "name"),)


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    alias_text: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    entity: Mapped["Entity"] = relationship(back_populates="alias_rows")

    __table_args__ = (UniqueConstraint("tenant_id", "entity_id", "alias_text", name="uq_entity_aliases_tenant_entity_alias"),)


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    mention_text: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    entity: Mapped["Entity | None"] = relationship(back_populates="mentions")
    message: Mapped["Message"] = relationship(back_populates="entity_mentions")  # noqa: F821
