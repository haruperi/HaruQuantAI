"""Unit tests for Analytics persistence statement builders."""

from __future__ import annotations

import pytest
from app.services.analytics.persistence import delete, update
from app.services.analytics.persistence.create import build_analytics_insert
from app.services.analytics.persistence.read import build_analytics_select


def test_build_analytics_insert_valid_table() -> None:
    """Insert builder generates parameterized SQL for allow-listed tables."""
    sql, params = build_analytics_insert(
        "analytics_journal_entries",
        {"record_id": "r1", "subject_id": "s1"},
    )
    assert "INSERT INTO analytics_journal_entries (record_id, subject_id)" in sql
    assert params == ("r1", "s1")


def test_build_analytics_insert_unsupported_table_or_empty_record() -> None:
    """Insert builder raises ValueError for unauthorized tables or empty records."""
    with pytest.raises(ValueError, match="unsupported Analytics insert"):
        build_analytics_insert("unauthorized_table", {"a": 1})

    with pytest.raises(ValueError, match="unsupported Analytics insert"):
        build_analytics_insert("analytics_journal_entries", {})


def test_build_analytics_select_valid_lookup() -> None:
    """Select builder generates parameterized lookup SQL for allow-listed tables."""
    sql, params = build_analytics_select(
        "analytics_journal_entries", "record_id", "entry-1"
    )
    assert sql == "SELECT * FROM analytics_journal_entries WHERE record_id = ?"
    assert params == ("entry-1",)


def test_build_analytics_select_unsupported_table_or_invalid_column() -> None:
    """Select builder raises ValueError for unallowed tables or invalid key columns."""
    with pytest.raises(ValueError, match="unsupported Analytics lookup"):
        build_analytics_select("unauthorized_table", "record_id", "entry-1")

    with pytest.raises(ValueError, match="unsupported Analytics lookup"):
        build_analytics_select("analytics_journal_entries", "col;DROP TABLE", "1")


def test_build_analytics_update_and_delete_unsupported() -> None:
    """Update and delete modules export empty __all__ as records are immutable."""
    assert delete.__all__ == ()
    assert update.__all__ == ()
