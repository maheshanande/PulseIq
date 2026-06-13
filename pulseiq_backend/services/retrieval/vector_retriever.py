import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.message import Message
from pulseiq_backend.repositories.event_repo import EmbeddingRepository
from pulseiq_backend.repositories.message_repo import MessageRepository
from pulseiq_backend.services.embeddings.embedding_service import embed_text


class VectorRetriever:
    def __init__(self, db: AsyncSession) -> None:
        self._embedding_repo = EmbeddingRepository(db)
        self._message_repo = MessageRepository(db)

    async def retrieve(self, tenant_id: uuid.UUID, question: str, limit: int = 10) -> list[Message]:
        query_vector = await embed_text(question)
        similar = await self._embedding_repo.search_similar(tenant_id, query_vector, limit)
        message_ids = [e.message_id for e in similar]
        return await self._message_repo.get_by_ids(tenant_id, message_ids)
