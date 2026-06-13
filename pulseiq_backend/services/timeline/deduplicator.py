from datetime import timedelta

from pulseiq_backend.models.event import Event, EventSource

# Events with same entity+type+status within this window = same business event
DEDUP_WINDOW = timedelta(hours=24)


class DeduplicatedEvent:
    def __init__(self, event: Event, sources: list[EventSource]) -> None:
        self.event = event
        self.sources = sources
        self.corroborating: list[tuple[Event, list[EventSource]]] = []

    @property
    def all_sources(self) -> list[EventSource]:
        extra = [s for _, srcs in self.corroborating for s in srcs]
        return self.sources + extra

    @property
    def reporter_count(self) -> int:
        return len(self.all_sources)


def deduplicate_events(
    event_tuples: list[tuple[Event, list[EventSource]]],
) -> list[DeduplicatedEvent]:
    """
    Group events that share the same entity_name, event_type, status
    and fall within DEDUP_WINDOW of each other.
    The earliest event is the canonical one; the rest are corroborating reports.
    """
    sorted_tuples = sorted(event_tuples, key=lambda t: t[0].created_at)
    groups: list[DeduplicatedEvent] = []

    for event, sources in sorted_tuples:
        key = (
            event.metadata_.get("entity_name", "").lower(),
            event.event_type.lower(),
            event.status.lower(),
        )
        matched = None
        for group in groups:
            g_key = (
                group.event.metadata_.get("entity_name", "").lower(),
                group.event.event_type.lower(),
                group.event.status.lower(),
            )
            if g_key == key and (event.created_at - group.event.created_at) <= DEDUP_WINDOW:
                matched = group
                break

        if matched:
            matched.corroborating.append((event, sources))
        else:
            groups.append(DeduplicatedEvent(event, sources))

    return groups
