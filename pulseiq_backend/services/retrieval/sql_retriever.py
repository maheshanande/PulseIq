import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.entity import Entity, EntityAlias, EntityMention
from pulseiq_backend.models.event import Event, EventSource
from pulseiq_backend.repositories.event_repo import EventRepository

_STOPWORDS = {"the", "this", "week", "was", "how", "is", "a", "an", "what", "are", "were", "of", "for"}
_OPEN_STATUS_TOKENS = {"active", "issue", "issues", "pending", "blocked", "down", "open", "delayed", "stuck", "problem", "problems"}
_CLOSED_STATUS_TOKENS = {"closed", "resolved", "shipped", "complete", "completed", "done", "paid"}
_ACTIVITY_SUMMARY_TOKENS = {"activity", "activities", "happened", "summary", "updates", "update", "performance"}


def _normalize(text: str) -> str:
    """Lowercase and strip special characters for fuzzy substring matching."""
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).strip()


def _tokens(text: str) -> set[str]:
    return set(_normalize(text).split())


def _identifiers(text: str) -> set[str]:
    return set(re.findall(r"\b(?:[a-z]+[-_#]?\d+[a-z0-9-]*|\d+[a-z0-9-]*)\b", text.lower()))


def _entity_query_score(candidate: str, question: str) -> int:
    candidate_normalized = _normalize(candidate)
    question_normalized = _normalize(question)
    if not candidate_normalized:
        return 0
    if candidate_normalized == question_normalized:
        return 100
    if candidate_normalized in question_normalized:
        return 90
    if question_normalized in candidate_normalized:
        return 80

    candidate_identifiers = _identifiers(candidate_normalized)
    question_identifiers = _identifiers(question_normalized)
    if candidate_identifiers and candidate_identifiers != question_identifiers:
        return 0

    candidate_tokens = _tokens(candidate_normalized)
    question_tokens = _tokens(question_normalized)
    if not candidate_tokens or not question_tokens:
        return 0

    shared_tokens = candidate_tokens & question_tokens
    shared_business_tokens = shared_tokens - _STOPWORDS
    if candidate_identifiers & question_identifiers and shared_business_tokens:
        return 70
    if len(shared_business_tokens) >= 2:
        return 50
    return 0


def _event_query_score(event: Event, question: str) -> int:
    question_tokens = _tokens(question) - _STOPWORDS
    if not question_tokens:
        return 0

    status_tokens = _tokens(event.status)
    event_type_tokens = _tokens(event.event_type)
    entity_tokens = _tokens(str(event.metadata_.get("entity_name", "")))

    if question_tokens & status_tokens:
        return 75
    if question_tokens & event_type_tokens:
        return 65
    if len(question_tokens & entity_tokens) >= 2:
        return 45
    return 0


def _asks_for_this_week(question: str) -> bool:
    normalized = _normalize(question)
    return "this week" in normalized or "week" in normalized


def _asks_for_activity_summary(question: str) -> bool:
    tokens = _tokens(question)
    return bool(tokens & _ACTIVITY_SUMMARY_TOKENS) or "how was" in _normalize(question)


def _asks_for_active_issues(question: str) -> bool:
    return bool(_tokens(question) & _OPEN_STATUS_TOKENS)


def _is_open_issue_event(event: Event) -> bool:
    event_tokens = _tokens(event.status) | _tokens(event.event_type)
    if event_tokens & _CLOSED_STATUS_TOKENS:
        return False
    return bool(event_tokens & _OPEN_STATUS_TOKENS)


class SQLRetriever:
    def __init__(self, db: AsyncSession) -> None:
        self._event_repo = EventRepository(db)
        self._db = db

    async def retrieve(self, tenant_id: uuid.UUID, question: str) -> list[tuple[Event, list[EventSource]]]:
        ranked_message_ids: list[tuple[int, uuid.UUID]] = []

        # Priority 1: exact/raw mention match. These are observations from messages, not canonical interpretations.
        mention_result = await self._db.execute(
            select(EntityMention).where(EntityMention.tenant_id == tenant_id)
        )
        for mention in mention_result.scalars().all():
            score = _entity_query_score(mention.mention_text, question)
            if score:
                ranked_message_ids.append((score, mention.message_id))

        if ranked_message_ids:
            matched_message_ids = [
                message_id
                for _, message_id in sorted(ranked_message_ids, key=lambda item: item[0], reverse=True)
            ]
            return await self._event_repo.get_by_message_ids(
                tenant_id,
                list(dict.fromkeys(matched_message_ids)),
            )

        # Priority 2: canonical names and aliases. These are query-time interpretations only.
        entity_result = await self._db.execute(
            select(Entity).where(Entity.tenant_id == tenant_id)
        )
        entities = entity_result.scalars().all()

        seen_entity_ids: set[uuid.UUID] = set()
        for entity in entities:
            candidates = [entity.name] + (entity.aliases or [])
            if any(_entity_query_score(candidate, question) for candidate in candidates) and entity.id not in seen_entity_ids:
                seen_entity_ids.add(entity.id)
                ranked_message_ids.extend(
                    (60, source.message_id)
                    for _, sources in await self._event_repo.get_by_entity(tenant_id, entity.id)
                    for source in sources
                )

        alias_result = await self._db.execute(
            select(EntityAlias).where(EntityAlias.tenant_id == tenant_id)
        )
        for alias in alias_result.scalars().all():
            if _entity_query_score(alias.alias_text, question) and alias.entity_id not in seen_entity_ids:
                seen_entity_ids.add(alias.entity_id)
                ranked_message_ids.extend(
                    (55, source.message_id)
                    for _, sources in await self._event_repo.get_by_entity(tenant_id, alias.entity_id)
                    for source in sources
                )

        # Priority 3: status/event category queries, e.g. "What is pending this week?"
        event_query = select(Event).where(Event.tenant_id == tenant_id)
        if _asks_for_this_week(question):
            event_query = event_query.where(Event.created_at >= datetime.now(timezone.utc) - timedelta(days=7))
        event_result = await self._db.execute(event_query)
        ranked_event_ids = [
            (score, event.id)
            for event in event_result.scalars().all()
            if (score := _event_query_score(event, question))
        ]
        if ranked_event_ids:
            event_ids = [
                event_id
                for _, event_id in sorted(ranked_event_ids, key=lambda item: item[0], reverse=True)
            ]
            event_tuples = await self._event_repo.get_by_event_ids(
                tenant_id,
                list(dict.fromkeys(event_ids)),
            )
            if event_tuples:
                return event_tuples

        # Priority 4: broad owner summaries, e.g. "activities this week" or "how was this week?"
        if _asks_for_activity_summary(question) or _asks_for_active_issues(question):
            summary_query = select(Event).where(Event.tenant_id == tenant_id)
            if _asks_for_this_week(question):
                summary_query = summary_query.where(Event.created_at >= datetime.now(timezone.utc) - timedelta(days=7))
            summary_query = summary_query.order_by(Event.created_at.desc()).limit(50)
            summary_result = await self._db.execute(summary_query)
            summary_events = list(summary_result.scalars().all())
            if _asks_for_active_issues(question):
                summary_events = [event for event in summary_events if _is_open_issue_event(event)]
            if summary_events:
                return await self._event_repo.get_by_event_ids(
                    tenant_id,
                    [event.id for event in summary_events],
                )

        matched_message_ids = [
            message_id
            for _, message_id in sorted(ranked_message_ids, key=lambda item: item[0], reverse=True)
        ]
        return await self._event_repo.get_by_message_ids(
            tenant_id,
            list(dict.fromkeys(matched_message_ids)),
        )
