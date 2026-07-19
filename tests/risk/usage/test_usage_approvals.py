"""Runnable usage examples for durable Risk approval tokens."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    DecisionState,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
)
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, 5, tzinfo=UTC)


class _AuditStore:
    """Minimal durable audit adapter for runnable examples."""

    def __init__(self) -> None:
        """Initialize empty example audit state."""
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Return the current example audit head.

        Args:
            timeout_seconds: Configured bounded timeout.

        Returns:
            Current record or None.
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
        """Append one exactly ordered example record.

        Args:
            record: Sealed record.
            expected_sequence: Required next sequence.
            expected_previous_hash: Required predecessor hash.
            timeout_seconds: Configured bounded timeout.

        Returns:
            Atomic append outcome.
        """
        del timeout_seconds
        head = self.records[-1] if self.records else None
        sequence = 0 if head is None else int(head.sequence or 0) + 1
        previous = "0" * 64 if head is None else str(head.record_hash)
        if sequence != expected_sequence or previous != expected_previous_hash:
            return "conflict"
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        """Return all example audit records.

        Args:
            timeout_seconds: Configured bounded timeout.

        Returns:
            Immutable ordered records.
        """
        del timeout_seconds
        return tuple(self.records)


class _TokenStore:
    """Minimal single-process durable token adapter for examples."""

    def __init__(self) -> None:
        """Initialize empty example token state."""
        self.tokens: dict[str, RiskApprovalToken] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()

    def save_issued(
        self,
        token: RiskApprovalToken,
        *,
        timeout_seconds: Decimal | None,
    ) -> Literal["saved", "already_saved", "conflict"]:
        """Save one issued example token.

        Args:
            token: Signed token.
            timeout_seconds: Configured bounded timeout.

        Returns:
            Atomic save outcome.
        """
        del timeout_seconds
        current = self.tokens.get(token.token_id)
        if current is None:
            self.tokens[token.token_id] = token
            return "saved"
        return "already_saved" if current == token else "conflict"

    def consume_if_active(
        self,
        token_id: str,
        *,
        expected_signature: str,
        reservation_id: str,
        workflow_id: str,
        action: str,
        scope: Mapping[str, str],
        now: datetime,
        timeout_seconds: Decimal | None,
    ) -> Literal[
        "consumed",
        "missing",
        "expired",
        "revoked",
        "already_consumed",
        "conflict",
    ]:
        """Consume one active exact example token.

        Args:
            token_id: Token identity.
            expected_signature: Required signature.
            reservation_id: Reservation identity.
            workflow_id: Bound workflow.
            action: Bound action.
            scope: Exact scope.
            now: Consumption time.
            timeout_seconds: Configured bounded timeout.

        Returns:
            Atomic state outcome.
        """
        del reservation_id, timeout_seconds
        token = self.tokens.get(token_id)
        if token is None:
            return "missing"
        if token_id in self.revoked:
            return "revoked"
        if token_id in self.consumed:
            return "already_consumed"
        if now >= token.expires_at:
            return "expired"
        if (
            token.signature != expected_signature
            or token.workflow_id != workflow_id
            or token.action != action
            or dict(token.scope) != dict(scope)
        ):
            return "conflict"
        self.consumed.add(token_id)
        return "consumed"

    def revoke_intersecting(
        self,
        scope: Mapping[str, str],
        *,
        reason: str,
        revoked_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> int:
        """Revoke outstanding tokens matching an example scope.

        Args:
            scope: Revocation selector.
            reason: Material reason.
            revoked_at: Revocation time.
            timeout_seconds: Configured bounded timeout.

        Returns:
            Number newly revoked.
        """
        del reason, revoked_at, timeout_seconds
        selected = {
            token_id
            for token_id, token in self.tokens.items()
            if token_id not in self.consumed
            and all(token.scope.get(key) == value for key, value in scope.items())
        }
        new = selected - self.revoked
        self.revoked.update(new)
        return len(new)


def _values(
    *, live: bool = False
) -> tuple[
    ApprovalTokenService,
    _TokenStore,
    RiskDecisionPackage,
    ApprovalAttestation,
]:
    """Build a complete independently runnable approval example.

    Args:
        live: Whether to use a fully bounded live profile.

    Returns:
        Service, state, eligible decision, and approval evidence.
    """
    config = RiskConfig(
        profile="live" if live else "research",
        execution_route="live" if live else "none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"audit": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=3 if live else None,
        var_lookback=3 if live else None,
        missing_calendar_mode="block" if live else None,
        audit_timeout_seconds=Decimal(5) if live else None,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        token_state_timeout_seconds=Decimal(5) if live else None,
        decision_ttl_seconds=Decimal(120),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
        double_spend_owner="risk_store" if live else None,
    )
    token_store = _TokenStore()
    audit = RiskAuditChain(config, _AuditStore(), lambda: NOW, canonical_json)
    service = ApprovalTokenService(
        config,
        token_store,
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "approver-1",
    )
    config_hash = compute_config_hash(config)
    decision = RiskDecisionPackage(
        decision_id="decision-1",
        intent_id="intent-1",
        state=DecisionState.APPROVE,
        requested_size=Decimal(10),
        approved_size=Decimal(8),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"portfolio": "snapshot-1"},
        config_hash=config_hash,
        concurrency_disclosure="risk_store",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=120),
        token=None,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    attestation = ApprovalAttestation(
        attestation_id="attestation-1",
        principal_id="approver-1",
        action="submit_order",
        scope={"account_id": "account-1", "symbol": "EURUSD"},
        policy_ref=config_hash,
        policy_version=config.policy_version,
        issued_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=120),
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )
    return service, token_store, decision, attestation


def _expected(token: RiskApprovalToken) -> dict[str, str]:
    """Build the exact documented execution-side expectation mapping."""
    return {
        "action": token.action,
        "decision_id": token.decision_id,
        "config_hash": token.config_hash,
        "request_id": token.request_id,
        "workflow_id": token.workflow_id,
        "correlation_id": token.correlation_id,
        **dict(token.scope),
    }


def test_usage_tokens_create_service() -> None:
    """Create a coordinator using injected state, audit, clock, and verifiers."""
    service, _, _, _ = _values()
    assert isinstance(service, ApprovalTokenService)


def test_usage_tokens_issue() -> None:
    """Issue a signed scoped token from an eligible approved decision."""
    service, store, decision, attestation = _values()
    token = service.issue(decision, attestation, now=NOW)
    assert store.tokens[token.token_id] == token


def test_usage_tokens_validate() -> None:
    """Validate and atomically consume a token before using its verdict."""
    service, _, decision, attestation = _values()
    token = service.issue(decision, attestation, now=NOW)
    result = service.validate_reserve_and_consume(
        token, attestation, _expected(token), now=NOW
    )
    assert result.valid is True
    assert result.action_policy_verdict is not None
    assert result.action_policy_verdict.allowed is True


def test_usage_tokens_revoke_scope() -> None:
    """Revoke outstanding tokens intersecting an activated control scope."""
    service, _, decision, attestation = _values()
    service.issue(decision, attestation, now=NOW)
    count = service.revoke_scope(
        {"account_id": "account-1"}, "kill switch activated", now=NOW
    )
    assert count == 1
