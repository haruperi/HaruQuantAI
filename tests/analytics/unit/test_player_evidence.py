"""Tests for FEAT-ANLT-07 through FEAT-ANLT-10."""

from datetime import UTC, datetime, timedelta

from app.services.analytics import (
    append_player_journal_entry,
    assess_plan_adherence,
    detect_behavior_patterns,
    evaluate_player_qualification,
)

from tests.analytics.usage._support import unwrap


def test_journal_is_idempotent_and_immutable() -> None:
    """Identical evidence replays and conflicting evidence fails closed."""
    values = {
        "session_id": "s",
        "plan_version": "v1",
        "author_id": "a",
        "occurred_at": datetime.now(UTC),
        "narrative": "bounded",
    }
    first = unwrap(append_player_journal_entry("entry_unit", **values))
    second = unwrap(append_player_journal_entry("entry_unit", **values))
    assert first["canonical_hash"] == second["canonical_hash"]
    assert (
        append_player_journal_entry(
            "entry_unit", **{**values, "narrative": "changed"}
        ).status
        == "error"
    )


def test_behavior_preserves_unavailable_and_versioned_thresholds() -> None:
    """Missing evidence stays unavailable and thresholds remain explicit."""
    adherence = unwrap(assess_plan_adherence({"stop": "set"}, [], plan_version="p1"))
    assert adherence["findings"][0]["status"] == "unavailable"
    behavior = unwrap(
        detect_behavior_patterns(
            [{"kind": "churn"}], threshold_version="t1", thresholds={"churn": 1}
        )
    )
    assert behavior["threshold_version"] == "t1"


def test_qualification_fails_closed_on_integrity_breach() -> None:
    """An integrity-breached pass requires remediation."""
    now = datetime.now(UTC)
    result = unwrap(
        evaluate_player_qualification(
            curriculum_version="v1",
            completed_prerequisites=("safe",),
            required_prerequisites=("safe",),
            attempts=({"passed": True, "integrity_breach": True},),
            valid_until=now + timedelta(days=1),
            now=now,
        )
    )
    assert result["status"] == "remediation_required"


def test_read_journal_entry_lookup_and_validation() -> None:
    """Lookup existing entry returns dict copy, absent returns None, invalid raises."""
    import pytest
    from app.services.analytics.contracts import AnalyticsValidationError
    from app.services.analytics.journal.service import read_journal_entry

    # Lookup appended entry
    entry = read_journal_entry("entry_unit")
    assert entry is not None
    assert entry["entry_id"] == "entry_unit"

    # Lookup non-existent entry
    assert read_journal_entry("non_existent_id") is None

    # Invalid entry_id raises AnalyticsValidationError
    with pytest.raises(AnalyticsValidationError, match="non-empty trimmed text"):
        read_journal_entry("")
