"""Integration test for Strategy-to-Risk operational eligibility review."""

from decimal import Decimal
from typing import Any, Literal

from app.services.risk import (
    create_risk_audit_chain,
    create_strategy_operational_eligibility_request,
    get_decision_state,
    review_strategy_admission,
    verify_risk_audit_chain,
)
from app.utils import canonical_json

from tests.risk import _support as examples


class _AuditStore:
    """Atomic in-memory durable store for integration audit evidence."""

    def __init__(self) -> None:
        """Initialize an empty chain."""
        self.records: list[Any] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> Any | None:
        """Return the current chain head.

        Args:
            timeout_seconds: Configured store timeout.

        Returns:
            Current head or None.
        """
        del timeout_seconds
        return self.records[-1] if self.records else None

    def append_atomic(
        self,
        record: Any,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Append an exact sequence-bound audit record.

        Args:
            record: Sealed record.
            expected_sequence: Required sequence.
            expected_previous_hash: Required predecessor hash.
            timeout_seconds: Configured store timeout.

        Returns:
            Atomic append outcome.
        """
        del expected_sequence, expected_previous_hash, timeout_seconds
        self.records.append(record)
        return "appended"

    def read_all(self, *, timeout_seconds: Decimal | None) -> tuple[Any, ...]:
        """Return all integration audit records.

        Args:
            timeout_seconds: Configured store timeout.

        Returns:
            Ordered sealed records.
        """
        del timeout_seconds
        return tuple(self.records)


def test_strategy_operational_eligibility_end_to_end() -> None:
    """Persist an exact Strategy decision and a verifiable sealed audit event."""
    config = examples._config()
    audit_store = _AuditStore()
    audit = create_risk_audit_chain(
        config,
        audit_store,
        lambda: examples.NOW,
        canonical_json,
    )
    eligibility_store = examples._EligibilityStore()
    decision = examples.unwrap_risk_response(
        review_strategy_admission(
            create_strategy_operational_eligibility_request(
                strategy_id="mean-reversion",
                strategy_version="1.0.0",
                runtime_profile="simulation",
                execution_route="sim",
                policy_version="policy-1",
                registration_ref=examples.HASH_B,
                evidence_refs={"market": examples.MARKET_REQUEST_ID},
                approval_refs=(),
                requested_scope={"symbol": "EURUSD"},
                requested_at=examples.NOW,
                request_id=examples.REQUEST_ID,
                workflow_id=examples.WORKFLOW_ID,
                correlation_id=examples.CORRELATION_ID,
            ),
            examples._registration(),
            examples._market(),
            config,
            eligibility_store,
            audit,
            now=examples.NOW,
        ),
        operation="review_strategy_admission",
    )
    assert decision.state is get_decision_state("APPROVE")
    assert eligibility_store.decision == decision
    assert (
        examples.unwrap_risk_response(
            verify_risk_audit_chain(audit, tuple(audit_store.records)),
            operation="risk_audit_chain.verify",
        )
        is True
    )
    assert audit_store.records[0].sealed is True
