import json
import logging
import re

from pydantic import ValidationError

from pulseiq_backend.schemas.event import ExtractedEntityMention, ExtractedEvent

logger = logging.getLogger(__name__)

_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def parse_extracted_event(raw: str) -> tuple[ExtractedEvent, list[ExtractedEntityMention]] | None:
    """Extract JSON from LLM output and validate with Pydantic. Returns None on failure."""
    match = _JSON_PATTERN.search(raw)
    if not match:
        logger.warning("No JSON found in LLM response: %s", raw[:200])
        return None
    try:
        data = json.loads(match.group())
        event = ExtractedEvent.model_validate(data)
        mentions = [
            ExtractedEntityMention.model_validate(entity)
            for entity in data.get("entities", [])
        ]
        if not mentions and event.entity_name:
            mentions = [
                ExtractedEntityMention(
                    mention_text=event.entity_name,
                    entity_type=event.entity_type,
                    confidence=event.confidence,
                )
            ]
        return event, mentions
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("LLM response failed validation: %s", exc)
        return None
