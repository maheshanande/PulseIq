from types import SimpleNamespace

from pulseiq_backend.services.entity_resolution.resolver import (
    canonicalize_entity_name,
    entity_identifiers,
    filter_identifier_compatible_entities,
)


def test_canonicalize_entity_name_preserves_machine_identifier() -> None:
    assert canonicalize_entity_name("Line/Machine 2") == "Line Machine 2"
    assert canonicalize_entity_name("machine-02") == "Machine 02"


def test_entity_identifiers_extracts_numeric_identifiers() -> None:
    assert entity_identifiers("Machine 2") == {"2"}
    assert entity_identifiers("Order PO-123") == {"po-123"}


def test_identifier_filter_blocks_wrong_machine_match() -> None:
    existing = [
        SimpleNamespace(name="Machine 1", aliases=[]),
        SimpleNamespace(name="Machine 2", aliases=[]),
    ]

    compatible = filter_identifier_compatible_entities("Machine 2", existing)

    assert [entity.name for entity in compatible] == ["Machine 2"]


def test_identifier_filter_treats_new_machine_id_as_new_entity() -> None:
    existing = [
        SimpleNamespace(name="Machine 1", aliases=[]),
        SimpleNamespace(name="Machine 3", aliases=[]),
    ]

    compatible = filter_identifier_compatible_entities("Machine 2", existing)

    assert compatible == []
