import uuid

from pulseiq_backend.models.message import Message
from pulseiq_backend.schemas.query import TimelineEntry
from pulseiq_backend.schemas.user import EMPLOYEE_DEPARTMENT_OPTIONS
from pulseiq_backend.services.timeline.deduplicator import DeduplicatedEvent


DEPARTMENT_LABELS = {
    option["value"]: option["label"] for option in EMPLOYEE_DEPARTMENT_OPTIONS
}


def format_message_user_label(msg: Message) -> str:
    if not msg.user:
        return "Unknown"

    name = msg.user.email.split("@")[0].capitalize()
    if msg.user.department:
        department = DEPARTMENT_LABELS.get(msg.user.department, msg.user.department)
        return f"{name} ({department})"
    return name


def _reporter_label(source_ids: list[uuid.UUID], message_map: dict[uuid.UUID, Message]) -> str:
    names = []
    for sid in source_ids:
        msg = message_map.get(sid)
        if msg and msg.user:
            names.append(format_message_user_label(msg))
    if not names:
        return "Operations Team"
    if len(names) == 1:
        return names[0]
    if len(names) <= 3:
        return ", ".join(names)
    return f"{', '.join(names[:2])} and {len(names) - 2} others"


def build_timeline(
    deduped_events: list[DeduplicatedEvent],
    message_map: dict[uuid.UUID, Message] | None = None,
) -> list[TimelineEntry]:
    message_map = message_map or {}
    entries: list[TimelineEntry] = []

    for deduped in sorted(deduped_events, key=lambda d: d.event.created_at):
        event = deduped.event
        source_ids = [s.message_id for s in deduped.all_sources]
        reporter = _reporter_label(source_ids, message_map)
        count = deduped.reporter_count

        event_label = event.event_type.replace("_", " ").capitalize()
        if count > 1:
            event_label = f"{event_label} (confirmed by {count} reporters)"

        entries.append(
            TimelineEntry(
                time=event.created_at.strftime("%d %b %Y %I:%M %p"),
                event=event_label,
                entity_name=event.metadata_.get("entity_name", "unknown"),
                reported_by=reporter,
                source_message_ids=source_ids,
            )
        )

    return entries
