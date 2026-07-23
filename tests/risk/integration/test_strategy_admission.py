"""Integration test for Strategy-to-Risk operational eligibility review."""

from decimal import Decimal
from typing import Literal

from app.services.risk.admission import review_strategy_admission
from app.services.risk.audit import RiskAuditChain
from app.services.risk.contracts import (
    DecisionState,
    RiskAuditRecord,
    StrategyOperationalEligibilityRequest,
)
from app.utils import canonical_json

from tests.risk import _support as examples


class _AuditStore:
    """Atomic in-memory durable store for integration audit evidence."""

    def __init__(self) -> None:
        """Initialize an empty chain."""
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
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
        record: RiskAuditRecord,
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

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
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
    audit = RiskAuditChain(config, audit_store, lambda: examples.NOW, canonical_json)
    eligibility_store = examples._EligibilityStore()
    decision = review_strategy_admission(
        StrategyOperationalEligibilityRequest(
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
            request_id="admission-integration-1",
            workflow_id="workflow-eligibility-1",
            correlation_id="correlation-1",
        ),
        examples._registration(),
        examples._market(),
        config,
        eligibility_store,
        audit,
        now=examples.NOW,
    )
    assert decision.state is DecisionState.APPROVE
    assert eligibility_store.decision == decision
    assert audit.verify(tuple(audit_store.records)) is True
    assert audit_store.records[0].sealed is True
