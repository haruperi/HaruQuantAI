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


def example_approvals() -> None:
    """Demonstrate Risk approval token lifecycle."""
    print("=" * 80)
    print("Risk Example 5: Approval Token Service")
    print("=" * 80)

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

    # 1. Issue token
    token = service.issue(decision, attestation, now=NOW)
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
    result = service.validate_reserve_and_consume(token, attestation, expected, now=NOW)
    print(f"Validation result valid: {result.valid}")


def main() -> None:
    """Run Risk approvals usage example."""
    example_approvals()


if __name__ == "__main__":
    main()
