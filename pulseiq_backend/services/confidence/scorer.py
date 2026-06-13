from pulseiq_backend.schemas.query import ConfidenceScore
from pulseiq_backend.services.timeline.deduplicator import DeduplicatedEvent


def calculate_confidence(
    deduped_events: list[DeduplicatedEvent],
    message_count: int,
) -> ConfidenceScore:
    """
    Confidence is derived from evidence quality, not LLM opinion.

    Factors:
    - source_weight:      more corroborating messages = higher confidence
    - event_weight:       having at least one clear structured event
    - consistency_bonus:  no conflicting statuses for same entity
    - penalty:            conflicting statuses detected
    """
    if not deduped_events and message_count == 0:
        return ConfidenceScore(score=0.0, label="Low")

    # Base: messages retrieved (capped contribution)
    source_weight = min(message_count * 0.08, 0.30)

    # Structured events found
    event_weight = min(len(deduped_events) * 0.20, 0.40)

    # Corroboration bonus — multiple reporters saying the same thing
    max_reporters = max((e.reporter_count for e in deduped_events), default=1)
    corroboration_bonus = min((max_reporters - 1) * 0.08, 0.20)

    # Conflict penalty — same entity, different statuses
    conflict_penalty = 0.0
    entity_statuses: dict[str, set[str]] = {}
    for e in deduped_events:
        name = e.event.metadata_.get("entity_name", "")
        entity_statuses.setdefault(name, set()).add(e.event.status.lower())
    for statuses in entity_statuses.values():
        if len(statuses) > 1:
            conflict_penalty += 0.15

    score = round(
        min(max(source_weight + event_weight + corroboration_bonus - conflict_penalty, 0.0), 1.0),
        2,
    )

    if score >= 0.75:
        label = "High"
    elif score >= 0.45:
        label = "Medium"
    else:
        label = "Low"

    return ConfidenceScore(score=score, label=label)
