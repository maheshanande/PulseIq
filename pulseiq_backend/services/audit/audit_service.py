import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.audit_log import AuditLog
from pulseiq_backend.models.query_session import QuerySession


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_session(self, tenant_id: uuid.UUID, question: str, user_id: uuid.UUID | None) -> QuerySession:
        session = QuerySession(tenant_id=tenant_id, question=question, user_id=user_id)
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def log(
        self,
        tenant_id: uuid.UUID,
        session_id: uuid.UUID,
        question: str,
        message_ids: list[uuid.UUID],
        event_ids: list[uuid.UUID],
        prompt: str,
        answer: str,
        confidence: float,
    ) -> None:
        log = AuditLog(
            tenant_id=tenant_id,
            query_session_id=session_id,
            question=question,
            retrieved_message_ids=[str(m) for m in message_ids],
            retrieved_event_ids=[str(e) for e in event_ids],
            prompt_used=prompt,
            answer=answer,
            confidence=confidence,
        )
        self._db.add(log)
        # Also update the session with final answer + confidence
        session = await self._db.get(QuerySession, session_id)
        if session:
            session.answer = answer
            session.confidence_score = round(confidence, 2)
        await self._db.commit()
