"""Unit tests for persistent Trading unknown-outcome resolution."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading.contracts import ExecutionReceipt
from app.services.trading.reconciliation import (
    AuthorityResolution,
    AuthoritySnapshot,
    resolve_unknown_outcome,
)
from app.services.trading.state import TradingEvent, TradingProjection
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _receipt() -> ExecutionReceipt:
    """Build one canonical unknown-outcome receipt."""
    return ExecutionReceipt(
        receipt_id="receipt-001",
        intent_id="intent-001",
        client_order_id="client-order-001",
        route="sim",
        authority="simulator",
        status="unknown_outcome",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal(0),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="timeout",
        retry_safe=False,
        reconciliation_required=True,
        request_id="request-001",
        correlation_id="correlation-001",
    )


def _attempt() -> TradingEvent:
    """Build originating persisted send-attempt evidence."""
    return TradingEvent(
        event_id="attempt-001",
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id="account-001",
        authority_id="simulator",
        occurred_at=NOW,
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        payload={"client_order_id": "client-order-001"},
    )


def _snapshot(*, orders: dict[str, object] | None = None) -> AuthoritySnapshot:
    """Build current Simulation authority evidence."""
    return AuthoritySnapshot(
        route="sim",
        authority_id="simulator",
        account_id="account-001",
        source_id="sim-read-001",
        account={"state": "ready"},
        orders=orders or {},
        positions={},
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
    )


class _Store:
    """Optimistic in-memory Trading store for resolution evidence."""

    def __init__(self, projection: TradingProjection) -> None:
        """Initialize projection and originating attempt evidence."""
        self.projection = projection
        self.events = [_attempt()]

    def load_projection(
        self,
        scope: tuple[object, str, str],
    ) -> TradingProjection | None:
        """Load the exact current projection."""
        current_scope = (
            self.projection.route,
            self.projection.tenant_id,
            self.projection.authority_id,
        )
        return self.projection if scope == current_scope else None

    def load_unresolved_attempts(
        self,
        scope: tuple[object, str, str],
    ) -> tuple[TradingEvent, ...]:
        """Load exact-scope unresolved send attempts."""
        del scope
        return tuple(
            event for event in self.events if event.event_type == "send_attempted"
        )

    def append_event(self, event: TradingEvent) -> None:
        """Append immutable reconciliation evidence."""
        self.events.append(event)

    def save_projection(
        self,
        projection: TradingProjection,
        expected_version: int,
    ) -> None:
        """Save a projection using optimistic version matching."""
        if self.projection.version != expected_version:
            raise RuntimeError("stale projection")
        self.projection = projection


def _projection(
    *,
    orders: dict[str, object] | None = None,
    authority_state: dict[str, object] | None = None,
) -> TradingProjection:
    """Build current Trading projection evidence."""
    return TradingProjection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulator",
        version=1,
        event_ids=("attempt-001",),
        orders=orders or {},
        positions={},
        fills={},
        receipts={},
        authority_state=authority_state or {},
        unresolved_attempt_ids=("attempt-001",),
        updated_at=NOW,
    )


def test_unknown_outcome_cannot_blind_retry() -> None:
    """Unresolved authority discrepancies persist and retain the retry lock."""
    store = _Store(_projection(orders={"order-internal": {"state": "pending"}}))
    resolution = resolve_unknown_outcome(  # type: ignore[arg-type]
        _receipt(),
        store,
        lambda _route: _snapshot(),
    )
    assert resolution.transition == "retry_locked"
    assert not resolution.retry_allowed
    assert resolution.remaining_unresolved_scope == ("order:order-internal",)
    assert [event.event_type for event in store.events[-2:]] == [
        "incident_recorded",
        "reconciliation_transitioned",
    ]


def test_resolution_requires_approved_transition() -> None:
    """Only exact stored approval can release a fully reconciled retry."""
    no_approval_store = _Store(_projection())
    no_approval = resolve_unknown_outcome(  # type: ignore[arg-type]
        _receipt(),
        no_approval_store,
        lambda _route: _snapshot(),
    )
    assert no_approval.transition == "resolved_no_retry"
    assert not no_approval.retry_allowed
    approved_store = _Store(
        _projection(
            authority_state={
                "approval": {
                    "receipt_id": "receipt-001",
                    "transition": "approved_retry",
                    "approved_transition_reference": "operator-approval-001",
                }
            }
        )
    )
    approved = resolve_unknown_outcome(  # type: ignore[arg-type]
        _receipt(),
        approved_store,
        lambda _route: _snapshot(),
    )
    assert approved.transition == "approved_retry"
    assert approved.retry_allowed
    with pytest.raises(ValidationError):
        AuthorityResolution(
            resolution_id="resolution-invalid",
            receipt_id="receipt-001",
            report_id="report-001",
            transition="approved_retry",
            retry_allowed=True,
            incident_reference="incident-001",
            approved_transition_reference=None,
            remaining_unresolved_scope=(),
        )
