import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.repositories.entity_repo import EntityRepository
from pulseiq_backend.repositories.event_repo import EventRepository, EmbeddingRepository
from pulseiq_backend.services.event_extraction.parser import parse_extracted_event
from pulseiq_backend.services.event_extraction.prompts import EVENT_EXTRACTION_PROMPT
from pulseiq_backend.services.llm import ollama_client
from pulseiq_backend.schemas.event import ExtractedEntityMention

logger = logging.getLogger(__name__)

_LINE_MACHINE_PATTERN = re.compile(r"\bline\s*/\s*machine\s*#?\s*([a-z0-9-]+)\b", re.IGNORECASE)
_MACHINE_PATTERN = re.compile(r"\bmachine\s*#?\s*([a-z0-9-]+)\b", re.IGNORECASE)
_PRODUCTION_LINE_PATTERN = re.compile(r"\b(?:production\s+line|line)\s*#?\s*([a-z0-9-]+)\b", re.IGNORECASE)


def infer_explicit_entity(content: str) -> ExtractedEntityMention | None:
    """Extract high-signal entity mentions from the original message evidence."""
    line_machine_match = _LINE_MACHINE_PATTERN.search(content)
    if line_machine_match:
        identifier = line_machine_match.group(1)
        return ExtractedEntityMention(mention_text=f"Machine {identifier}", entity_type="machine", confidence=0.99)

    machine_match = _MACHINE_PATTERN.search(content)
    if machine_match:
        identifier = machine_match.group(1)
        return ExtractedEntityMention(mention_text=f"Machine {identifier}", entity_type="machine", confidence=0.99)

    production_line_match = _PRODUCTION_LINE_PATTERN.search(content)
    if production_line_match:
        identifier = production_line_match.group(1)
        return ExtractedEntityMention(mention_text=f"Production Line {identifier}", entity_type="production_line", confidence=0.99)

    return None


def apply_deterministic_entity_guard(extracted, mentions: list[ExtractedEntityMention], content: str):
    explicit_entity = infer_explicit_entity(content)
    if explicit_entity is None:
        return extracted, mentions

    if extracted.entity_type != explicit_entity.entity_type or extracted.entity_name.lower() != explicit_entity.mention_text.lower():
        logger.info(
            "Overriding extracted entity %s/%s with explicit message entity %s/%s",
            extracted.entity_type,
            extracted.entity_name,
            explicit_entity.entity_type,
            explicit_entity.mention_text,
        )

    guarded_mentions = [
        mention
        for mention in mentions
        if not (
            mention.entity_type == explicit_entity.entity_type
            and mention.mention_text.lower() != explicit_entity.mention_text.lower()
        )
    ]
    if not any(
        mention.entity_type == explicit_entity.entity_type
        and mention.mention_text.lower() == explicit_entity.mention_text.lower()
        for mention in guarded_mentions
    ):
        guarded_mentions.insert(0, explicit_entity)

    guarded_event = extracted.model_copy(
        update={
            "entity_type": explicit_entity.entity_type,
            "entity_name": explicit_entity.mention_text,
            "aliases": [],
        }
    )
    return guarded_event, guarded_mentions


class EventExtractor:
    def __init__(self, db: AsyncSession) -> None:
        self._entity_repo = EntityRepository(db)
        self._event_repo = EventRepository(db)
        self._embedding_repo = EmbeddingRepository(db)

    async def process_message(self, tenant_id: uuid.UUID, message_id: uuid.UUID, content: str) -> None:
        prompt = EVENT_EXTRACTION_PROMPT.format(message=content)
        raw = await ollama_client.generate(prompt)
        parsed = parse_extracted_event(raw)

        if parsed is None:
            logger.info("Skipping unparseable event for message %s", message_id)
            return

        extracted, mentions = parsed

        if extracted.confidence < 0.4:
            logger.info("Skipping low-confidence or unparseable event for message %s", message_id)
            return

        extracted, mentions = apply_deterministic_entity_guard(extracted, mentions, content)

        # Store raw observations. Do not resolve, normalize, merge, or create canonical entities during ingestion.
        for mention in mentions:
            await self._entity_repo.add_mention(
                tenant_id=tenant_id,
                message_id=message_id,
                mention_text=mention.mention_text,
                entity_type=mention.entity_type,
                confidence=mention.confidence,
            )

        primary_mention = mentions[0] if mentions else None

        # Persist event (immutable) with observation metadata only.
        event = await self._event_repo.create(
            tenant_id=tenant_id,
            event_type=extracted.event_type,
            status=extracted.status,
            confidence=extracted.confidence,
            metadata={
                "entity_name": primary_mention.mention_text if primary_mention else extracted.entity_name,
                "entity_type": primary_mention.entity_type if primary_mention else extracted.entity_type,
                "entity_mentions": [
                    {
                        "mention_text": mention.mention_text,
                        "entity_type": mention.entity_type,
                        "confidence": mention.confidence,
                    }
                    for mention in mentions
                ],
            },
        )

        # Link event back to source message
        await self._event_repo.link_source(tenant_id, event.id, message_id)

        # Generate and store embedding
        embedding = await ollama_client.embed(content)
        await self._embedding_repo.create(tenant_id, message_id, embedding)

        logger.info("Processed message %s → event %s (entity mention: %s)", message_id, event.id, event.metadata_.get("entity_name"))
