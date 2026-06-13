import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.event import Event, EventSource
from pulseiq_backend.models.message import Message
from pulseiq_backend.services.retrieval.sql_retriever import SQLRetriever
from pulseiq_backend.services.retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    def __init__(self, db: AsyncSession) -> None:
        self._sql = SQLRetriever(db)
        self._vector = VectorRetriever(db)

    async def retrieve(
        self, tenant_id: uuid.UUID, question: str
    ) -> tuple[list[tuple[Event, list[EventSource]]], list[Message]]:
        event_tuples = await self._sql.retrieve(tenant_id, question)
        messages = await self._vector.retrieve(tenant_id, question)

        seen: set[uuid.UUID] = set()
        unique_messages: list[Message] = []
        for msg in messages:
            if msg.id not in seen:
                seen.add(msg.id)
                unique_messages.append(msg)

        return event_tuples, unique_messages
