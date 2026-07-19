"""Unit tests for the durable Risk approval-token lifecycle."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Lock
from typing import Literal

import pytest
from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.approvals.state import _TokenStateStore
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    ApprovalAttestation,
    DecisionState,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
)
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, 5, tzinfo=UTC)
KEY = b"risk-approval-test-key-material-32-bytes"


class _AuditStore:
    """Atomic in-memory audit store for approval unit tests."""

    def __init__(self) -> None:
        """Initialize an empty test audit chain."""
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
        """Return the current test audit head."""
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
        """Append a record when its expected predecessor is current."""
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
        """Return all test audit records."""
        del timeout_seconds
        return tuple(self.records)


class _TokenStore:
    """Lock-protected durable-state model for approval unit tests."""

    def __init__(self) -> None:
        """Initialize empty token, consumption, and revocation state."""
        self.tokens: dict[str, RiskApprovalToken] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()
        self._lock = Lock()

    def save_issued(
        self,
        token: RiskApprovalToken,
        *,
        timeout_seconds: Decimal | None,
    ) -> Literal["saved", "already_saved", "conflict"]:
        """Save one exact token once."""
        del timeout_seconds
        with self._lock:
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
        scope: dict[str, str] | object,
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
        """Consume exactly one active matching test token."""
        del reservation_id, timeout_seconds
        with self._lock:
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
                or dict(token.scope) != dict(scope)  # type: ignore[arg-type]
            ):
                return "conflict"
            self.consumed.add(token_id)
            return "consumed"

    def revoke_intersecting(
        self,
        scope: dict[str, str] | object,
        *,
        reason: str,
        revoked_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> int:
        """Revoke every outstanding intersecting test token."""
        del reason, revoked_at, timeout_seconds
        selector = dict(scope)  # type: ignore[arg-type]
        with self._lock:
            matching = {
                token_id
                for token_id, token in self.tokens.items()
                if token_id not in self.consumed
                and all(
                    token.scope.get(key) == value for key, value in selector.items()
                )
            }
            new = matching - self.revoked
            self.revoked.update(new)
            return len(new)


def _config() -> RiskConfig:
    """Build deterministic approval unit-test policy."""
    return RiskConfig(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"audit": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(120),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )


def _decision(config: RiskConfig) -> RiskDecisionPackage:
    """Build one eligible approving Risk decision."""
    return RiskDecisionPackage(
        decision_id="decision-1",
        intent_id="intent-1",
        state=DecisionState.APPROVE,
        requested_size=Decimal(10),
        approved_size=Decimal(8),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"portfolio": "snapshot-1"},
        config_hash=compute_config_hash(config),
        concurrency_disclosure="risk_store",
        recommendations=(),
        issued_at=NOW,
        expires_at=NOW + timedelta(seconds=120),
        token=None,
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )


def _attestation(config: RiskConfig) -> ApprovalAttestation:
    """Build exact authorized UI approval evidence."""
    return ApprovalAttestation(
        attestation_id="attestation-1",
        principal_id="approver-1",
        action="submit_order",
        scope={"account_id": "account-1", "symbol": "EURUSD"},
        policy_ref=compute_config_hash(config),
        policy_version=config.policy_version,
        issued_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(seconds=120),
        request_id="request-1",
        workflow_id="workflow-1",
        correlation_id="correlation-1",
    )


def _service(
    config: RiskConfig, token_store: _TokenStore, audit_store: _AuditStore
) -> ApprovalTokenService:
    """Build one fully injected approval unit-test service."""
    audit = RiskAuditChain(config, audit_store, lambda: NOW, canonical_json)
    return ApprovalTokenService(
        config,
        token_store,
        audit,
        lambda: NOW,
        lambda reference: KEY if reference == "secrets/risk-key" else b"",
        lambda attestation: attestation.principal_id == "approver-1",
    )


def _expected(token: RiskApprovalToken) -> dict[str, str]:
    """Build the exact documented receiver-owned token expectation."""
    return {
        "action": token.action,
        "decision_id": token.decision_id,
        "config_hash": token.config_hash,
        "request_id": token.request_id,
        "workflow_id": token.workflow_id,
        "correlation_id": token.correlation_id,
        **dict(token.scope),
    }


def test_service_never_exposes_key() -> None:
    """Retain only a resolver and never expose resolved signing key bytes."""
    config = _config()
    service = _service(config, _TokenStore(), _AuditStore())
    assert KEY not in service.__dict__.values()
    assert KEY.decode() not in repr(service.__dict__)


def test_issue_requires_valid_ui_approval_attestation() -> None:
    """Bind issuance to exact current externally authorized approval evidence."""
    config = _config()
    store = _TokenStore()
    audit_store = _AuditStore()
    service = _service(config, store, audit_store)
    invalid = _attestation(config).model_copy(update={"principal_id": "intruder"})
    with pytest.raises(RiskDomainError) as captured:
        service.issue(_decision(config), invalid, now=NOW)
    assert captured.value.risk_code is RiskErrorCode.PERMISSION_DENIED
    token = service.issue(_decision(config), _attestation(config), now=NOW)
    assert token.token_id in store.tokens
    assert audit_store.records[-1].event_type == "risk.approval_token.issued"


def test_concurrent_reservation_succeeds_once() -> None:
    """Allow one atomic reservation and fail every competing consumption."""
    config = _config()
    store = _TokenStore()
    service = _service(config, store, _AuditStore())
    attestation = _attestation(config)
    token = service.issue(_decision(config), attestation, now=NOW)

    def consume() -> str:
        """Attempt one concurrent token consumption."""
        try:
            result = service.validate_reserve_and_consume(
                token, attestation, _expected(token), now=NOW
            )
            return "consumed" if result.valid else "invalid"
        except RiskDomainError as error:
            return error.risk_code.value

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: consume(), range(2)))
    assert outcomes.count("consumed") == 1
    assert outcomes.count(RiskErrorCode.APPROVAL_TOKEN_CONSUMED.value) == 1


def test_kill_switch_revokes_affected_scope() -> None:
    """Revoke every affected outstanding token and reject later consumption."""
    config = _config()
    store = _TokenStore()
    service = _service(config, store, _AuditStore())
    attestation = _attestation(config)
    token = service.issue(_decision(config), attestation, now=NOW)
    assert (
        service.revoke_scope(
            {"account_id": "account-1"}, "kill switch activated", now=NOW
        )
        == 1
    )
    with pytest.raises(RiskDomainError) as captured:
        service.validate_reserve_and_consume(
            token, attestation, _expected(token), now=NOW
        )
    assert captured.value.risk_code is RiskErrorCode.APPROVAL_TOKEN_REVOKED


def test_tampered_token_fails_closed_before_consumption() -> None:
    """Reject signature tampering without creating an allowed verdict."""
    config = _config()
    store = _TokenStore()
    service = _service(config, store, _AuditStore())
    attestation = _attestation(config)
    token = service.issue(_decision(config), attestation, now=NOW)
    tampered = token.model_copy(update={"signature": "0" * 64})
    with pytest.raises(RiskDomainError) as captured:
        service.validate_reserve_and_consume(
            tampered, attestation, _expected(tampered), now=NOW
        )
    assert captured.value.risk_code is RiskErrorCode.APPROVAL_TOKEN_INVALID
    assert token.token_id not in store.consumed


def test_private_state_contract_is_abstract() -> None:
    """Keep every private durable-state operation receiver-implemented."""
    token = RiskApprovalToken.model_construct()
    with pytest.raises(NotImplementedError):
        _TokenStateStore.save_issued(
            object(),
            token,
            timeout_seconds=None,  # type: ignore[arg-type]
        )
    with pytest.raises(NotImplementedError):
        _TokenStateStore.consume_if_active(
            object(),  # type: ignore[arg-type]
            "token-1",
            expected_signature="signature",
            reservation_id="reservation-1",
            workflow_id="workflow-1",
            action="submit_order",
            scope={"account_id": "account-1"},
            now=NOW,
            timeout_seconds=None,
        )
    with pytest.raises(NotImplementedError):
        _TokenStateStore.revoke_intersecting(
            object(),  # type: ignore[arg-type]
            {"account_id": "account-1"},
            reason="test",
            revoked_at=NOW,
            timeout_seconds=None,
        )
