"""Unit tests for validation taxonomy."""

from datetime import UTC, datetime

import pytest
from app.utils import build_validation_outcome, combine_validation_outcomes
from app.utils.errors.exceptions import ValidationError


def test_unknown_outranks_warn_and_empty_set_raises() -> None:
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    warn = build_validation_outcome(
        verdict="WARN",
        check_id="warn",
        evaluated_at=instant,
        reason_codes=["DATA.STALE"],
        severity="WARNING",
    )
    unknown = build_validation_outcome(
        verdict="UNKNOWN",
        check_id="unknown",
        evaluated_at=instant,
        reason_codes=["STATE.UNKNOWN"],
        severity="ERROR",
    )
    assert combine_validation_outcomes([warn, unknown])["verdict"] == "UNKNOWN"
    with pytest.raises(ValidationError):
        combine_validation_outcomes([])
