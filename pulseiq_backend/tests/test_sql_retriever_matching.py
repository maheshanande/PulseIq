from types import SimpleNamespace

from pulseiq_backend.services.retrieval.sql_retriever import (
    _asks_for_active_issues,
    _asks_for_activity_summary,
    _entity_query_score,
    _event_query_score,
    _is_open_issue_event,
)


def test_line_question_matches_production_line_mention() -> None:
    assert _entity_query_score("Production Line 2", "How was Line 2 this week?") > 0


def test_different_line_numbers_do_not_match() -> None:
    assert _entity_query_score("Production Line 1", "How was Line 2 this week?") == 0


def test_machine_numbers_do_not_cross_match() -> None:
    assert _entity_query_score("Machine 1", "What happened to Machine 2?") == 0


def test_pending_question_matches_pending_status() -> None:
    event = SimpleNamespace(status="pending", event_type="payment_pending", metadata_={"entity_name": "Sharma"})

    assert _event_query_score(event, "What is pending this week?") > 0


def test_pending_question_matches_payment_pending_event_type() -> None:
    event = SimpleNamespace(status="open", event_type="payment_pending", metadata_={"entity_name": "Sharma"})

    assert _event_query_score(event, "What is pending this week?") > 0


def test_broad_activity_questions_are_detected() -> None:
    assert _asks_for_activity_summary("activities this week")
    assert _asks_for_activity_summary("how was this week?")


def test_active_issue_questions_are_detected() -> None:
    assert _asks_for_active_issues("Which customers have active issues?")


def test_open_issue_event_excludes_closed_events() -> None:
    open_event = SimpleNamespace(status="pending", event_type="payment_pending")
    closed_event = SimpleNamespace(status="paid", event_type="payment_pending")

    assert _is_open_issue_event(open_event)
    assert not _is_open_issue_event(closed_event)
