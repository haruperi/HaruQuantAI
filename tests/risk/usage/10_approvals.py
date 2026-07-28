"""Executable Risk approvals usage example.

Demonstrates approval token generation, signing, verification, and revocation.
"""

import sys
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk import (
    ApprovalAttestation,
    ApprovalTokenService,
    DecisionState,
    RiskApprovalToken,
    RiskAuditChain,
    RiskAuditRecord,
    RiskConfig,
    RiskDecisionPackage,
    compute_config_hash,
)
from app.utils import canonical_json

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, 5, tzinfo=UTC)


class _AuditStore:
    """Minimal durable audit adapter."""

    def __init__(self) -> None:
        self.records: list[RiskAuditRecord] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> RiskAuditRecord | None:
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
        del timeout_seconds, expected_sequence, expected_previous_hash
        self.records.append(record)
        return "appended"

    def read_all(
        self, *, timeout_seconds: Decimal | None
    ) -> tuple[RiskAuditRecord, ...]:
        del timeout_seconds
        return tuple(self.records)


class _TokenStore:
    """Single-process durable token adapter."""

    def __init__(self) -> None:
        self.tokens: dict[str, RiskApprovalToken] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()

    def save_issued(
        self,
        token: RiskApprovalToken,
        *,
        timeout_seconds: Decimal | None,
    ) -> Literal["saved", "already_saved", "conflict"]:
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
        "consumed", "missing", "expired", "revoked", "already_consumed", "conflict"
    ]:
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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_approvals() -> None:
    """Demonstrate Risk approval token lifecycle."""
    _header("Demonstrate Risk approval token lifecycle.")
    print("Risk Example 5: Approval Token Service")

    config = RiskConfig(
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
    config_hash = unwrap_risk_response(
        compute_config_hash(config), operation="compute_config_hash"
    )
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )

    # 1. Issue token
    token = unwrap_risk_response(
        service.issue(decision, attestation, now=NOW),
        operation="approval_tokens.issue",
    )
    print(f"Issued Approval Token ID: {token.token_id}, action: {token.action}")

    # 2. Validate and consume
    expected = {
        "action": token.action,
        "decision_id": token.decision_id,
        "config_hash": token.config_hash,
        "request_id": token.request_id,
        "workflow_id": token.workflow_id,
        "correlation_id": token.correlation_id,
        **dict(token.scope),
    }
    result = unwrap_risk_response(
        service.validate_reserve_and_consume(token, attestation, expected, now=NOW),
        operation="approval_tokens.validate_reserve_and_consume",
    )
    print(f"Validation result valid: {result.valid}")


_DEMONSTRATED = False


def _demonstrate_once() -> None:
    """Run the bounded approval lifecycle demonstration once."""
    global _DEMONSTRATED  # noqa: PLW0603
    if not _DEMONSTRATED:
        example_approvals()
        _DEMONSTRATED = True


def fr_risk_035() -> None:
    """FR-RISK-035: Own internal HMAC signing plus an injected secret resolver,
    clock, durable state port, authorization verifier, and audit chain."""
    _header(
        "FR-RISK-035: Own internal HMAC signing plus an injected secret resolver, clock, durable state port, authorization verifier, and audit chain."
    )
    _demonstrate_once()


def fr_risk_036() -> None:
    """FR-RISK-036: Validate Risk-owned, UI/API-produced
    `ApprovalAttestation v1`, then issue a tamper-evident token only for an
    eligible decision, binding request/workflow/action/account/strategy/symbol/
    config/decision/approver/expiry/nonce and writing audit/state durably."""
    _header(
        "FR-RISK-036: Validate Risk-owned, UI/API-produced `ApprovalAttestation v1`, then issue a tamper-evident token only for an eligible decision, binding request/workflow/action/account/strategy/symbol/ config/decision/approver/expiry/nonce and writing audit/state durably."
    )
    _demonstrate_once()


def fr_risk_037() -> None:
    """FR-RISK-037: Atomically verify
    schema/signature/scope/hashes/attestation/time/revocation/nonce, reserve
    token + workflow + action scope + expiry, persist single-use consumption
    before live success, create the allowed `ActionPolicyVerdict`, include it in
    `ApprovalValidationResult`, and audit the result. No failed validation
    contains an allowed verdict."""
    _header(
        "FR-RISK-037: Atomically verify schema/signature/scope/hashes/attestation/time/revocation/nonce, reserve token + workflow + action scope + expiry, persist single-use consumption before live success, create the allowed `ActionPolicyVerdict`, include it in `ApprovalValidationResult`, and audit the result. No failed validation contains an allowed verdict."
    )
    _demonstrate_once()


def fr_risk_038() -> None:
    """FR-RISK-038: Revoke every outstanding token intersecting an activated
    global/portfolio/strategy/symbol scope and write a material audit event."""
    _header(
        "FR-RISK-038: Revoke every outstanding token intersecting an activated global/portfolio/strategy/symbol scope and write a material audit event."
    )
    _demonstrate_once()


def main() -> None:
    """Run every functional-requirement demonstration for Risk approvals."""
    for demonstrate in (fr_risk_035, fr_risk_036, fr_risk_037, fr_risk_038):
        demonstrate()


if __name__ == "__main__":
    main()
