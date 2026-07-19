"""Unit tests for deterministic Trading authority comparison."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta

import pytest
from app.services.trading.reconciliation import (
    AuthoritySnapshot,
    ReconciliationReport,
    compare_authority_state,
)
from app.services.trading.state import TradingProjection
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _snapshot() -> AuthoritySnapshot:
    """Build authority facts containing missing and mismatched records."""
    return AuthoritySnapshot(
        route="sim",
        authority_id="simulator",
        account_id="account-001",
        source_id="sim-read-001",
        account={"state": "ready"},
        orders={
            "order-shared": {"state": "filled"},
            "order-authority": {"state": "open"},
        },
        positions={},
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )


def _projection() -> TradingProjection:
    """Build conflicting Trading projection facts."""
    return TradingProjection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulator",
        version=2,
        orders={
            "order-shared": {"state": "open"},
            "order-internal": {"state": "pending"},
        },
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )


def test_unresolved_mismatch_stays_unresolved() -> None:
    """Missing and mismatched facts remain explicit and unresolved."""
    report = compare_authority_state(_snapshot(), _projection())
    assert report.unresolved
    assert report.severity == "critical"
    assert report.missing_internal_ids == ("order:order-authority",)
    assert report.missing_authority_ids == ("order:order-internal",)
    assert report.mismatched_ids == ("order:order-shared",)


def test_report_cannot_claim_false_resolution() -> None:
    """A discrepancy-bearing report cannot claim resolved status."""
    valid = compare_authority_state(_snapshot(), _projection())
    data = valid.model_dump()
    data["unresolved"] = False
    with pytest.raises(ValidationError):
        ReconciliationReport.model_validate(data)
