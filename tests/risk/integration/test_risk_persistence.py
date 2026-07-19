"""Workflow integration test for fail-closed Risk audit and token state."""

from decimal import Decimal
from typing import Literal

import pytest
from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.audit import RiskAuditChain
from app.services.risk.contracts import (
    DecisionState,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
)
from app.utils import canonical_json

from tests.risk.usage import test_usage_approvals as approval_examples
from tests.risk.usage import test_usage_decisions as decision_examples
from tests.risk.usage import test_usage_policy as policy_examples


class _UnavailableAuditStore:
    """Receiver adapter whose durable audit backend is unavailable."""

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Fail the first mandatory audit read.

        Args:
            timeout_seconds: Configured bounded timeout.

        Raises:
            OSError: Always, to model backend unavailability.
        """
        del timeout_seconds
        raise OSError("audit unavailable")

    def append_atomic(
        self,
        record: RiskAuditRecord,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Reject unreachable append operation.

        Args:
            record: Sealed record.
            expected_sequence: Required sequence.
            expected_previous_hash: Required predecessor hash.
            timeout_seconds: Configured bounded timeout.

        Raises:
            OSError: Always, to model backend unavailability.
        """
        del record, expected_sequence, expected_previous_hash, timeout_seconds
        raise OSError("audit unavailable")

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        """Reject unreachable full-chain read.

        Args:
            timeout_seconds: Configured bounded timeout.

        Raises:
            OSError: Always, to model backend unavailability.
        """
        del timeout_seconds
        raise OSError("audit unavailable")


def _eligible_decision(config_hash: str) -> RiskDecisionPackage:
    """Build one exact eligible decision for persistence failure workflow.

    Args:
        config_hash: Active exact Risk config hash.

    Returns:
        Token-eligible canonical Risk decision.
    """
    config = decision_examples._config()
    governor, _, _ = decision_examples._services(config)
    pending = governor.review_trade_risk(
        decision_examples._proposal(config),
        decision_examples._snapshot(config),
        policy_examples._market(),
        decision_examples._regime(),
        (decision_examples._inactive_state(),),
        decision_examples._auth(config),
        now=decision_examples.NOW,
    )
    values = pending.model_dump(mode="python")
    values.update(
        state=DecisionState.APPROVE,
        approved_size=pending.requested_size,
        primary_failure_limit=None,
        composite_breach_flags=(),
        recommendations=(),
        config_hash=config_hash,
        evidence_refs={**pending.evidence_refs, "config": config_hash},
    )
    return RiskDecisionPackage.model_validate(values)


def test_audit_and_token_state_fail_closed_atomically() -> None:
    """Expose no successful issue when mandatory audit persistence fails."""
    config = decision_examples._config()
    token_store = approval_examples._TokenStore()
    audit = RiskAuditChain(
        config, _UnavailableAuditStore(), lambda: decision_examples.NOW, canonical_json
    )
    service = ApprovalTokenService(
        config,
        token_store,
        audit,
        lambda: decision_examples.NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    with pytest.raises(RiskDomainError) as captured:
        service.issue(
            _eligible_decision(policy_examples.compute_config_hash(config)),
            decision_examples._attestation(config),
            now=decision_examples.NOW,
        )
    assert captured.value.risk_code is RiskErrorCode.STORAGE_ERROR
    assert len(token_store.tokens) == 1
    assert all(
        isinstance(token, RiskApprovalToken) for token in token_store.tokens.values()
    )
