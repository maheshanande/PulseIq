import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.repositories.message_repo import MessageRepository
from pulseiq_backend.schemas.query import QueryRequest, QueryResponse, SourceEntry, ReasoningBlock
from pulseiq_backend.services.audit.audit_service import AuditService
from pulseiq_backend.services.confidence.scorer import calculate_confidence
from pulseiq_backend.services.llm.answer_generator import generate_answer
from pulseiq_backend.services.retrieval.hybrid_retriever import HybridRetriever
from pulseiq_backend.services.timeline.deduplicator import deduplicate_events
from pulseiq_backend.services.timeline.timeline_builder import format_message_user_label


class QueryOrchestrator:
    def __init__(self, db: AsyncSession) -> None:
        self._retriever = HybridRetriever(db)
        self._audit = AuditService(db)
        self._message_repo = MessageRepository(db)

    async def answer(self, request: QueryRequest) -> QueryResponse:
        session = await self._audit.create_session(
            request.tenant_id, request.question, request.user_id
        )

        event_tuples, vector_messages = await self._retriever.retrieve(request.tenant_id, request.question)

        # event_source_ids are the ground truth — directly linked to retrieved events
        event_source_ids: list[uuid.UUID] = list(dict.fromkeys(
            s.message_id for _, sources in event_tuples for s in sources
        ))

        # Re-fetch only event-linked messages with user relationship
        # Vector search results are used for LLM context but NOT for sources display
        messages = await self._message_repo.get_by_ids_with_user(request.tenant_id, event_source_ids)
        message_ids = event_source_ids

        # Deduplicate before confidence scoring
        deduped = deduplicate_events(event_tuples)

        # Confidence from evidence — not from LLM
        confidence = calculate_confidence(deduped, len(messages))

        summary, current_status, assessment, timeline, prompt = await generate_answer(
            question=request.question,
            event_tuples=event_tuples,
            messages=messages,  # event-linked messages for display + LLM context
        )

        # Build sources block with content and submitted_by
        message_map = {m.id: m for m in messages}
        sources = [
            SourceEntry(
                message_id=m.id,
                submitted_by=format_message_user_label(m),
                content=m.content,
            )
            for m in sorted(messages, key=lambda x: x.created_at)
        ]

        # Reasoning block
        entities = list({
            e.event.metadata_.get("entity_name")
            for e in deduped
            if e.event.metadata_.get("entity_name")
        })
        reasoning = ReasoningBlock(
            messages_analyzed=len(messages),
            events_found=len(deduped),
            entity=entities[0] if len(entities) == 1 else (", ".join(entities) if entities else None),
        )

        event_ids = [event.id for event, _ in event_tuples]

        await self._audit.log(
            tenant_id=request.tenant_id,
            session_id=session.id,
            question=request.question,
            message_ids=message_ids,
            event_ids=event_ids,
            prompt=prompt,
            answer=summary,
            confidence=confidence.score,
        )

        return QueryResponse(
            executive_summary=summary,
            current_status=current_status,
            assessment=assessment,
            confidence=confidence,
            timeline=timeline,
            sources=sources,
            reasoning=reasoning,
        )
