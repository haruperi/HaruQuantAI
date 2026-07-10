"""Unit tests for the pre-mutation audit recording gate primitive."""
# ruff: noqa: ARG002

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.trading.contracts import JsonObject
from app.services.trading.gates.audit_and_compensation import record_pre_mutation_audit
from app.services.trading.security.error_mapping import TradingMappedError

NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class WorkingAuditSink:
    """Audit sink double that always succeeds."""

    def append(self, *, event: JsonObject, recorded_at: datetime) -> str:
        """Return a synthetic audit reference."""
        return "audit-ref-1"

    def flush(self) -> None:
        """No-op flush."""
        return


class FailingAuditSink:
    """Audit sink double that always fails."""

    def append(self, *, event: JsonObject, recorded_at: datetime) -> str:
        """Raise to simulate a durability failure."""
        raise OSError("disk full")

    def flush(self) -> None:
        """No-op flush."""
        return


def test_record_pre_mutation_audit_returns_reference_on_success() -> None:
    """A successful audit write returns its reference."""
    reference = record_pre_mutation_audit(
        audit_sink=WorkingAuditSink(), event={"action": "submit_order"}, recorded_at=NOW
    )
    assert reference == "audit-ref-1"


def test_record_pre_mutation_audit_blocks_on_write_failure() -> None:
    """An audit write failure blocks the mutation with a mapped error."""
    with pytest.raises(TradingMappedError) as exc_info:
        record_pre_mutation_audit(
            audit_sink=FailingAuditSink(),
            event={"action": "submit_order"},
            recorded_at=NOW,
        )
    assert exc_info.value.code == "LIVE_AUDIT_WRITE_FAILED"
