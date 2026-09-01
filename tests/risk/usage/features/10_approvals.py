"""Executable Risk approvals usage example.

Demonstrates FEAT-RISK-10 approval token generation, signing, verification, and revocation.
"""

from __future__ import annotations

import sys
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.serialization import canonical_json
from app.services.risk import (
    compute_config_hash,
    create_approval_attestation,
    create_approval_token_service,
    create_risk_audit_chain,
    create_risk_config,
    create_risk_decision_package,
    get_decision_state,
    issue_risk_approval_token,
    revoke_risk_approval_scope,
    validate_risk_approval_token,
)
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, 5, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class _AuditStore:
    """Minimal durable audit adapter."""

    def __init__(self) -> None:
        self.records: list[Any] = []

    def read_head(self, *, timeout_seconds: Decimal | None) -> Any | None:
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
        del timeout_seconds, expected_sequence, expected_previous_hash
        self.records.append(record)
        return "appended"

    def read_all(self, *, timeout_seconds: Decimal | None) -> tuple[Any, ...]:
        del timeout_seconds
        return tuple(self.records)


class _TokenStore:
    """Single-process durable token adapter."""

    def __init__(self) -> None:
        self.tokens: dict[str, Any] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()

    def save_issued(
        self,
        token: Any,
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


def _setup_service():
    config = create_risk_config(
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
    audit = create_risk_audit_chain(config, _AuditStore(), lambda: NOW, canonical_json)
    service = create_approval_token_service(
        config,
        token_store,
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "approver-1",
    )
    return service, config, token_store


def fr_risk_035() -> None:
    """FR-RISK-035: Stage 1 — Own internal HMAC signing plus an injected secret resolver, clock, durable state port, authorization verifier, and audit chain."""
    _header("Stage 1: Approval Token Service - Service Setup (FR-RISK-035)")
    print("SUCCESS: FR-RISK-035")
    service, _, _ = _setup_service()
    print(_format_result(service))
    print(
        "Data -> Approval token service configured with HMAC signing and injected dependencies"
    )


def fr_risk_036() -> None:
    """FR-RISK-036: Stage 3 — Validate Risk-owned, UI/API-produced `create_approval_attestation v1`, then issue a tamper-evident token only for an eligible decision, binding request/workflow/action/account/strategy/symbol/ config/decision/approver/expiry/nonce and writing audit/state durably."""
    _header("Stage 3: Token Issuance - Issue Approval Token (FR-RISK-036)")
    print("SUCCESS: FR-RISK-036")
    service, config, _ = _setup_service()
    config_hash = unwrap_risk_response(
        compute_config_hash(config), operation="compute_config_hash"
    )
    decision = create_risk_decision_package(
        decision_id="decision-1",
        intent_id="intent-1",
        state=get_decision_state("APPROVE"),
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
    attestation = create_approval_attestation(
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
    token = unwrap_risk_response(
        issue_risk_approval_token(service, decision, attestation, now=NOW),
        operation="issue_risk_approval_token",
    )
    print(_format_result(token))
    print(f"Data -> token_id='{token.token_id}', action='{token.action}'")


def fr_risk_037() -> None:
    """FR-RISK-037: Stage 3 — Atomically verify schema/signature/scope/hashes/attestation/time/revocation/nonce, reserve token + workflow + action scope + expiry, persist single-use consumption before live success, create the allowed `ActionPolicyVerdict`, include it in `ApprovalValidationResult`, and audit the result. No failed validation contains an allowed verdict."""
    _header(
        "Stage 3: Token Validation & Consumption - Validate Approval Token (FR-RISK-037)"
    )
    print("SUCCESS: FR-RISK-037")
    service, config, _ = _setup_service()
    config_hash = unwrap_risk_response(
        compute_config_hash(config), operation="compute_config_hash"
    )
    decision = create_risk_decision_package(
        decision_id="decision-1",
        intent_id="intent-1",
        state=get_decision_state("APPROVE"),
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
    attestation = create_approval_attestation(
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
    token = unwrap_risk_response(
        issue_risk_approval_token(service, decision, attestation, now=NOW),
        operation="issue_risk_approval_token",
    )
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
        validate_risk_approval_token(
            service,
            token,
            attestation,
            expected,
            now=NOW,
        ),
        operation="validate_risk_approval_token",
    )
    print(_format_result(result))
    print(f"Data -> valid={result.valid}, consumed={result.consumed}")


def fr_risk_038() -> None:
    """FR-RISK-038: Stage 3 — Revoke every outstanding token intersecting an activated global/portfolio/strategy/symbol scope and write a material audit event."""
    _header("Stage 3: Scope Revocation - Revoke Approval Scope (FR-RISK-038)")
    print("SUCCESS: FR-RISK-038")
    service, config, _ = _setup_service()
    config_hash = unwrap_risk_response(
        compute_config_hash(config), operation="compute_config_hash"
    )
    decision = create_risk_decision_package(
        decision_id="decision-1",
        intent_id="intent-1",
        state=get_decision_state("APPROVE"),
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
    attestation = create_approval_attestation(
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
    unwrap_risk_response(
        issue_risk_approval_token(service, decision, attestation, now=NOW),
        operation="issue_risk_approval_token",
    )
    revoked_count = unwrap_risk_response(
        revoke_risk_approval_scope(
            service,
            {"symbol": "EURUSD"},
            reason="Emergency revocation",
            now=NOW,
        ),
        operation="revoke_risk_approval_scope",
    )
    print(_format_result(revoked_count))
    print(f"Data -> revoked_count={revoked_count}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-10 — approvals/ — Risk Approval Token Lifecycle\n\n"
        "Purpose: Issue, validate, consume, and revoke signed scoped approval tokens through durable state.\n\n"
        "Module flow:\n"
        "-> Stage 1: Initialize approval token service and build inputs\n"
        "-> Stage 2: Validate HMAC signature, token expiry, and attestation binding\n"
        "-> Stage 3: Return RiskApprovalToken, ActionPolicyVerdict, and revoked token counts"
    )
    fr_risk_035()
    fr_risk_036()
    fr_risk_037()
    fr_risk_038()


if __name__ == "__main__":
    main()
