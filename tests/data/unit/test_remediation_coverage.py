"""Focused coverage for small Data boundary modules."""

import pytest
from app.services.data import (
    get_calendar_dashboard_snapshot,
    get_market_hours_dashboard_snapshot,
)
from app.services.data.contracts import DataError
from app.services.data.persistence import delete
from app.services.data.persistence.contracts import (
    TransactionRequest,
    TransactionResult,
)
from app.services.data.persistence.dataset_writer import _raise_manifest_field_error
from app.utils import generate_id


def test_market_hours_dashboard_reports_explicit_missing_scope() -> None:
    """Return bounded unavailable evidence instead of inventing a market."""
    snapshot = get_market_hours_dashboard_snapshot()
    assert snapshot["status"] == "unavailable"
    assert snapshot["reason"] == "MARKET_SCOPE_REQUIRED"


def test_calendar_dashboard_reports_explicit_missing_scope() -> None:
    """Return bounded unavailable evidence instead of inventing calendar scope."""
    snapshot = get_calendar_dashboard_snapshot()
    assert snapshot["status"] == "unavailable"
    assert snapshot["reason"] == "CALENDAR_SCOPE_REQUIRED"


def test_invalid_dataset_manifest_field_fails_closed() -> None:
    """Reject absent provenance through the canonical corruption error."""
    with pytest.raises(DataError) as captured:
        _raise_manifest_field_error("source_revision", generate_id("req"))
    assert captured.value.code == "FILE_CORRUPTED"


def test_delete_cache_records_delegates_one_bounded_statement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Delegate explicit cache keys through the transaction boundary."""
    captured: dict[str, TransactionRequest] = {}

    def execute(request: TransactionRequest) -> TransactionResult:
        captured["request"] = request
        return TransactionResult(
            rows=(), affected_rows=2, committed=True, request_id=request.request_id
        )

    monkeypatch.setattr(delete, "_execute_transaction_raw", execute)
    result = delete.delete_cache_records(("a", "b"), request_id=generate_id("req"))
    assert result.affected_rows == 2
    request = captured["request"]
    assert request.plan.parameter_sets == (("a", "b"),)
