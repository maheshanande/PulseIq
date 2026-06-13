import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.event import Event, EventSource
from pulseiq_backend.models.entity import EntityMention
from pulseiq_backend.models.embedding import MessageEmbedding


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        tenant_id: uuid.UUID,
        event_type: str,
        status: str,
        confidence: float,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        event = Event(
            tenant_id=tenant_id,
            event_type=event_type,
            status=status,
            confidence=confidence,
            metadata_=metadata or {},
        )
        self._db.add(event)
        await self._db.commit()
        await self._db.refresh(event)
        return event

    async def link_source(self, tenant_id: uuid.UUID, event_id: uuid.UUID, message_id: uuid.UUID) -> None:
        source = EventSource(tenant_id=tenant_id, event_id=event_id, message_id=message_id)
        self._db.add(source)
        await self._db.commit()

    async def get_by_entity(self, tenant_id: uuid.UUID, entity_id: uuid.UUID) -> list[tuple[Event, list[EventSource]]]:
        """Returns list of (event, sources) tuples — avoids ORM lazy-load issues."""
        mention_result = await self._db.execute(
            select(EntityMention.message_id)
            .where(EntityMention.tenant_id == tenant_id, EntityMention.entity_id == entity_id)
        )
        message_ids = [row[0] for row in mention_result.all()]
        if not message_ids:
            return []

        source_result = await self._db.execute(
            select(EventSource)
            .where(EventSource.tenant_id == tenant_id, EventSource.message_id.in_(message_ids))
        )
        all_sources = list(source_result.scalars().all())
        event_ids = list({s.event_id for s in all_sources})
        if not event_ids:
            return []

        event_result = await self._db.execute(
            select(Event)
            .where(Event.tenant_id == tenant_id, Event.id.in_(event_ids))
            .order_by(Event.created_at)
        )
        events = list(event_result.scalars().all())

        sources_by_event: dict[uuid.UUID, list[EventSource]] = {}
        for s in all_sources:
            sources_by_event.setdefault(s.event_id, []).append(s)

        return [(event, sources_by_event.get(event.id, [])) for event in events]

    async def get_by_message_ids(self, tenant_id: uuid.UUID, message_ids: list[uuid.UUID]) -> list[tuple[Event, list[EventSource]]]:
        """Returns events linked to raw mention-matched messages."""
        if not message_ids:
            return []

        source_result = await self._db.execute(
            select(EventSource)
            .where(EventSource.tenant_id == tenant_id, EventSource.message_id.in_(message_ids))
        )
        all_sources = list(source_result.scalars().all())
        event_ids = list({s.event_id for s in all_sources})
        if not event_ids:
            return []

        event_result = await self._db.execute(
            select(Event)
            .where(Event.tenant_id == tenant_id, Event.id.in_(event_ids))
            .order_by(Event.created_at)
        )
        events = list(event_result.scalars().all())

        sources_by_event: dict[uuid.UUID, list[EventSource]] = {}
        for source in all_sources:
            sources_by_event.setdefault(source.event_id, []).append(source)

        return [(event, sources_by_event.get(event.id, [])) for event in events]

    async def get_by_event_ids(self, tenant_id: uuid.UUID, event_ids: list[uuid.UUID]) -> list[tuple[Event, list[EventSource]]]:
        """Returns events and sources for direct event/status retrieval."""
        if not event_ids:
            return []

        event_result = await self._db.execute(
            select(Event)
            .where(Event.tenant_id == tenant_id, Event.id.in_(event_ids))
            .order_by(Event.created_at)
        )
        events = list(event_result.scalars().all())
        if not events:
            return []

        source_result = await self._db.execute(
            select(EventSource)
            .where(EventSource.tenant_id == tenant_id, EventSource.event_id.in_([event.id for event in events]))
        )
        all_sources = list(source_result.scalars().all())

        sources_by_event: dict[uuid.UUID, list[EventSource]] = {}
        for source in all_sources:
            sources_by_event.setdefault(source.event_id, []).append(source)

        return [(event, sources_by_event.get(event.id, [])) for event in events]

    async def get_recent(self, tenant_id: uuid.UUID, limit: int = 100) -> list[Event]:
        result = await self._db.execute(
            select(Event)
            .where(Event.tenant_id == tenant_id)
            .options(joinedload(Event.sources))
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
        return list(result.unique().scalars().all())


class EmbeddingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, tenant_id: uuid.UUID, message_id: uuid.UUID, embedding: list[float]) -> MessageEmbedding:
        emb = MessageEmbedding(tenant_id=tenant_id, message_id=message_id, embedding=embedding)
        self._db.add(emb)
        await self._db.commit()
        await self._db.refresh(emb)
        return emb

    async def search_similar(self, tenant_id: uuid.UUID, query_vector: list[float], limit: int = 10) -> list[MessageEmbedding]:
        """Cosine similarity search scoped to tenant."""
        result = await self._db.execute(
            select(MessageEmbedding)
            .where(MessageEmbedding.tenant_id == tenant_id)
            .order_by(MessageEmbedding.embedding.cosine_distance(query_vector))
            .limit(limit)
        )
        return list(result.scalars().all())
