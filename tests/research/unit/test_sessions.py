"""Unit tests for Research session resolution (FR-RES-069 to 072)."""

from datetime import time

import pandas as pd
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    active_sessions_for_hour,
    create_research_value,
    session_hours_payload,
    session_label_for_hour,
    tag_sessions,
)

logger = get_logger(__name__)


def _config() -> object:
    """Build a two-session policy with a documented overlap."""
    return create_research_value(
        "SessionConfig",
        "UTC",
        {
            "london": (time(8), time(17)),
            "new_york": (time(13), time(22)),
        },
        ("london", "new_york"),
    )


def _cross_midnight_config() -> object:
    """Build a session policy with a cross-midnight window."""
    return create_research_value(
        "SessionConfig",
        "UTC",
        {
            "sydney": (time(22), time(7)),
            "london": (time(8), time(17)),
        },
        ("london", "sydney"),
    )


def test_active_sessions_handles_overlap() -> None:
    """FR-RES-069: both overlapping sessions are returned in precedence."""
    logger.debug("Testing Research active sessions overlap")
    active = active_sessions_for_hour(14, config=_config())
    assert active == ("london", "new_york")


def test_active_sessions_returns_single_when_no_overlap() -> None:
    """FR-RES-069: only one session is returned outside overlap."""
    active = active_sessions_for_hour(9, config=_config())
    assert active == ("london",)


def test_session_label_uses_precedence() -> None:
    """FR-RES-070: primary label follows overlap precedence."""
    logger.debug("Testing Research session label precedence")
    assert session_label_for_hour(14, config=_config()) == "london"


def test_session_label_returns_unmatched_for_gap() -> None:
    """FR-RES-070: gaps resolve to unmatched."""
    assert session_label_for_hour(3, config=_config()) == "unmatched"


def test_session_payload_is_versioned() -> None:
    """FR-RES-071: payload carries schema version and overlap evidence."""
    logger.debug("Testing Research session-hours payload")
    payload = session_hours_payload(config=_config())
    assert payload["schema_version"] == "v1"
    assert payload["timezone"] == "UTC"
    assert "london+new_york" in payload["overlaps"]


def test_active_sessions_rejects_invalid_hour() -> None:
    """FR-RES-069: invalid hour fails closed."""
    with pytest.raises(ValueError, match="INVALID_HOUR_OF_DAY"):
        active_sessions_for_hour(24, config=_config())


def test_tag_sessions_handles_cross_midnight() -> None:
    """FR-RES-072: cross-midnight windows tag correctly without reordering."""
    logger.debug("Testing Research cross-midnight session tagging")
    idx = pd.date_range("2026-01-01", periods=24, freq="h", tz="UTC")
    data = pd.DataFrame({"close": range(24)}, index=idx)
    tagged, _warnings = tag_sessions(data, config=_cross_midnight_config())
    assert "session" in tagged.columns
    assert list(tagged.index) == list(data.index)
    assert "sydney" in set(tagged["session"].to_numpy())
    assert "london" in set(tagged["session"].to_numpy())


def test_tag_sessions_rejects_naive_index() -> None:
    """FR-RES-072: naive timestamps fail closed."""
    idx = pd.date_range("2026-01-01", periods=5, freq="h")
    data = pd.DataFrame({"close": range(5)}, index=idx)
    with pytest.raises(ValueError, match="NAIVE_INDEX_REJECTED"):
        tag_sessions(data, config=_config())
