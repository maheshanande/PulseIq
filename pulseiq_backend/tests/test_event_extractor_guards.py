from pulseiq_backend.schemas.event import ExtractedEvent
from pulseiq_backend.services.event_extraction.extractor import (
    apply_deterministic_entity_guard,
    infer_explicit_entity,
)


def test_infer_line_machine_entity_from_message() -> None:
    mention = infer_explicit_entity("Line/Machine 2 is down for 3 hours")

    assert mention is not None
    assert mention.entity_type == "machine"
    assert mention.mention_text == "Machine 2"


def test_explicit_machine_overrides_wrong_llm_entity() -> None:
    extracted = ExtractedEvent(
        entity_type="machine",
        entity_name="Machine 1",
        aliases=[],
        event_type="line_down",
        status="down",
        confidence=0.91,
    )

    guarded, mentions = apply_deterministic_entity_guard(
        extracted,
        [],
        "Line/Machine 2 is down for 3hours because the power grid was short circuted.",
    )

    assert guarded.entity_type == "machine"
    assert guarded.entity_name == "Machine 2"
    assert guarded.aliases == []
    assert mentions[0].mention_text == "Machine 2"
