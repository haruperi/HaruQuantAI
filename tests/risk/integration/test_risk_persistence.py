"""Workflow integration test for fail-closed Risk audit and token state."""

from datetime import timedelta
from decimal import Decimal
from typing import Any, Literal

from app.kernel.serialization import canonical_json
from app.services.risk import (
    apply_kill_switch_command,
    compute_config_hash,
    create_approval_attestation,
    create_approval_token_service,
    create_kill_switch_command,
    create_risk_audit_chain,
    create_risk_decision_package,
    get_decision_state,
    issue_risk_approval_token,
    review_trade_risk,
)

from tests.risk import _support as approval_examples
from tests.risk import _support as decision_examples
from tests.risk import _support as policy_examples


class _UnavailableAuditStore:
    """Receiver adapter whose durable audit backend is unavailable."""

    def read_head(self, *, timeout_seconds: Decimal | None) -> Any | None:
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
        record: Any,
        *,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["appended", "already_appended", "conflict"]:
        """Reject unreachable append operation."""
        del record, expected_sequence, expected_previous_hash, timeout_seconds
        raise OSError("audit unavailable")

    def read_all(self, *, timeout_seconds: Decimal | None) -> tuple[Any, ...]:
        """Reject unreachable full-chain read."""
        del timeout_seconds
        raise OSError("audit unavailable")


class _UnavailableKillSwitchStore(approval_examples._KillStore):
    """Combined adapter that fails before an atomic transition can commit."""

    def compare_and_swap_with_audit(
        self,
        state: Any,
        record: Any,
        *,
        expected_version: int,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["committed", "already_committed", "conflict"]:
        """Fail the combined state-and-audit transaction before mutation."""
        del (
            state,
            record,
            expected_version,
            expected_sequence,
            expected_previous_hash,
            timeout_seconds,
        )
        raise OSError("transaction unavailable")


def _eligible_decision(config_hash: str) -> Any:
    """Build one exact eligible decision for persistence failure workflow.

    Args:
        config_hash: Active exact Risk config hash.

    Returns:
        Token-eligible canonical Risk decision.
    """
    config = decision_examples._config()
    governor, _, _ = decision_examples._services(config)
    pending = decision_examples.unwrap_risk_response(
        review_trade_risk(
            governor,
            decision_examples._proposal(config),
            decision_examples._snapshot(config),
            policy_examples._market(),
            decision_examples._regime(),
            (decision_examples._inactive_state(),),
            decision_examples._auth(config),
            now=decision_examples.NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )
    values = pending.model_dump(warnings=False, mode="python")
    values.update(
        state=get_decision_state("APPROVE"),
        approved_size=pending.requested_size,
        primary_failure_limit=None,
        composite_breach_flags=(),
        recommendations=(),
        config_hash=config_hash,
        evidence_refs={**pending.evidence_refs, "config": config_hash},
    )
    return create_risk_decision_package(**values)


def test_audit_and_token_state_fail_closed_atomically() -> None:
    """Expose no successful issue when mandatory audit persistence fails."""
    config = decision_examples._config()
    token_store = approval_examples._TokenStore()
    audit = create_risk_audit_chain(
        config, _UnavailableAuditStore(), lambda: decision_examples.NOW, canonical_json
    )
    service = create_approval_token_service(
        config,
        token_store,
        audit,
        lambda: decision_examples.NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    response = issue_risk_approval_token(
        service,
        _eligible_decision(
            decision_examples.unwrap_risk_response(
                policy_examples.compute_config_hash(config),
                operation="compute_config_hash",
            )
        ),
        decision_examples._attestation(config),
        now=decision_examples.NOW,
    )
    assert response.status == "error"
    assert response.error.code == "STORAGE_ERROR"
    assert len(token_store.tokens) == 1
    assert all(token.token_id for token in token_store.tokens.values())


def test_kill_switch_clearance_audit_failure_leaves_state_unchanged() -> None:
    """Expose no cleared state when the atomic state/audit transaction fails."""
    config = decision_examples._config()
    _, approvals, _ = decision_examples._services(config)
    store = _UnavailableKillSwitchStore()
    audit = create_risk_audit_chain(
        config,
        store,
        lambda: decision_examples.NOW,
        canonical_json,
    )
    current = decision_examples._inactive_state().model_copy(
        update={"state": "active", "reason": "operator safety stop"}
    )
    command = create_kill_switch_command(
        action="clear",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="reconciled and independently approved",
        requested_at=decision_examples.NOW,
        request_id=decision_examples.REQUEST_ID,
        workflow_id=decision_examples.WORKFLOW_ID,
        correlation_id=decision_examples.CORRELATION_ID,
    )
    attestation = create_approval_attestation(
        attestation_id="clearance-independent-1",
        principal_id="operator-2",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref=decision_examples.unwrap_risk_response(
            compute_config_hash(config), operation="compute_config_hash"
        ),
        policy_version=config.policy_version,
        issued_at=decision_examples.NOW,
        expires_at=decision_examples.NOW + timedelta(minutes=1),
        request_id=decision_examples.REQUEST_ID,
        workflow_id=decision_examples.WORKFLOW_ID,
        correlation_id=decision_examples.CORRELATION_ID,
    )

    response = apply_kill_switch_command(
        command,
        current,
        decision_examples._auth(config, clearance=True),
        approvals,
        audit,
        store,
        config,
        attestation=attestation,
        now=decision_examples.NOW,
    )
    assert response.status == "error"
    assert response.error.code == "STORAGE_ERROR"
    assert store.state is None
    assert store.records == []
