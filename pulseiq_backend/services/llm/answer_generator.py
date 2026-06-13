import logging
import re
import uuid

from pulseiq_backend.models.event import Event, EventSource
from pulseiq_backend.models.message import Message
from pulseiq_backend.schemas.query import TimelineEntry
from pulseiq_backend.services.event_extraction.prompts import QUERY_ANSWER_PROMPT
from pulseiq_backend.services.llm import ollama_client
from pulseiq_backend.services.timeline.deduplicator import deduplicate_events
from pulseiq_backend.services.timeline.timeline_builder import build_timeline, format_message_user_label

logger = logging.getLogger(__name__)

_SECTION_RE = re.compile(
    r"SUMMARY\s*(.*?)\s*CURRENT_STATUS\s*(.*?)\s*ASSESSMENT\s*(.*?)$",
    re.DOTALL | re.IGNORECASE,
)


def _parse_response(raw: str) -> tuple[str, str | None, str | None]:
    match = _SECTION_RE.search(raw)
    if match:
        return (
            match.group(1).strip(),
            match.group(2).strip() or None,
            match.group(3).strip() or None,
        )
    logger.warning("LLM response did not match structured format")
    return raw.strip(), None, None


async def generate_answer(
    question: str,
    event_tuples: list[tuple[Event, list[EventSource]]],
    messages: list[Message],
) -> tuple[str, str | None, str | None, list[TimelineEntry], str]:
    """Returns (summary, current_status, assessment, timeline_entries, prompt_used)."""
    message_map: dict[uuid.UUID, Message] = {m.id: m for m in messages}
    deduped = deduplicate_events(event_tuples)
    timeline = build_timeline(deduped, message_map)

    timeline_text = "\n".join(
        f"{e.time} | {e.entity_name} | {e.event} | reported by {e.reported_by}"
        for e in timeline
    ) or "No structured events found."

    messages_text = "\n".join(
        f"[MSG-{str(m.id)[:8].upper()}]"
        + (f" {format_message_user_label(m)}" if m.user else "")
        + f": {m.content}"
        for m in sorted(messages, key=lambda x: x.created_at)
    ) or "No source messages found."

    prompt = QUERY_ANSWER_PROMPT.format(
        question=question,
        timeline=timeline_text,
        messages=messages_text,
    )

    raw_answer = await ollama_client.generate(prompt)
    summary, current_status, assessment = _parse_response(raw_answer)
    return summary, current_status, assessment, timeline, prompt
