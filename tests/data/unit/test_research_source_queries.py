"""Unit evidence for FEAT-DATA-16 decision-time query validation."""

from datetime import UTC, datetime

from app.services.data import (
    build_research_source_query,
    get_research_source_value_field,
)


def test_query_preserves_decision_time_and_bounds() -> None:
    """Preserve exact point-in-time query evidence."""
    decision_time = datetime(2026, 1, 1, tzinfo=UTC)
    query = build_research_source_query(
        decision_time=decision_time,
        source_kinds=("macro",),
        asset_scope=("EURUSD",),
        limit=25,
    )

    assert get_research_source_value_field(query, "decision_time") == decision_time
    assert get_research_source_value_field(query, "limit") == 25
