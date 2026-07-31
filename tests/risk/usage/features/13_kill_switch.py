"""Executable Risk kill-switch usage example.

Demonstrates FEAT-RISK-13 authorized kill-switch activation and canonical block-state checking.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import (
    apply_kill_switch_command,
    check_risk_kill_switch,
    create_approval_token_service,
    create_kill_switch_command,
    create_kill_switch_state,
    create_risk_audit_chain,
    create_risk_config,
)
from app.utils import canonical_json, create_auth_context, generate_id
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = generate_id("req")
WORKFLOW_ID = generate_id("wf")
CORRELATION_ID = generate_id("cor")


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
    """Single-process token store."""

    def __init__(self) -> None:
        self.tokens: dict[str, Any] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()

    def save_issued(self, token: Any, *, timeout_seconds: Decimal | None) -> str:
        del timeout_seconds
        self.tokens[token.token_id] = token
        return "saved"

    def revoke_intersecting(
        self,
        scope: dict[str, str],
        *,
        reason: str,
        revoked_at: datetime,
        timeout_seconds: Decimal | None,
    ) -> int:
        del scope, reason, revoked_at, timeout_seconds
        return 0


class _KillStore(_AuditStore):
    """Atomic version-exact canonical state and audit adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.state: create_kill_switch_state | None = None

    def compare_and_swap_with_audit(
        self,
        state: create_kill_switch_state,
        record: Any,
        *,
        expected_version: int,
        expected_sequence: int,
        expected_previous_hash: str,
        timeout_seconds: Decimal | None,
    ) -> Literal["committed", "already_committed", "conflict"]:
        del timeout_seconds
        current = expected_version if self.state is None else self.state.version
        head = self.records[-1] if self.records else None
        sequence = 0 if head is None else int(head.sequence or 0) + 1
        previous = "0" * 64 if head is None else str(head.record_hash)
        if self.state == state and head == record:
            return "already_committed"
        if (
            current != expected_version
            or sequence != expected_sequence
            or previous != expected_previous_hash
        ):
            return "conflict"
        self.state = state
        self.records.append(record)
        return "committed"


def _setup():
    config = create_risk_config(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"portfolio": 60, "audit": 60},
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )

    auth = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="operator-1",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("risk.kill.activate", "risk.kill.clear"),
        scopes=("risk",),
        tenant_or_environment=config.profile,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        issued_at=NOW,
    )

    kill_store = _KillStore()
    audit = create_risk_audit_chain(config, kill_store, lambda: NOW, canonical_json)
    token_store = _TokenStore()
    approvals = create_approval_token_service(
        config,
        token_store,
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    inactive_state = create_kill_switch_state(
        state_id="global-state-1",
        scope_level="global",
        scope={},
        state="inactive",
        reason="normal operation",
        version=1,
        updated_at=NOW,
    )
    return config, auth, kill_store, audit, approvals, inactive_state


def fr_risk_043() -> None:
    """FR-RISK-043: Stage 3 — Apply an authorized, version-checked activation/clearance under `global > portfolio > strategy > symbol` precedence, atomically compare-and-swap canonical state with its Risk audit record in the injected store, revoke affected approvals on activation, and never mutate execution controls. Activation requires one authorized `create_auth_context` and remains immediate and unilateral. Clearance additionally requires a matching current `create_approval_attestation v1` from a different authorized principal; same-principal clearance leaves the active state unchanged and fails deterministically. Active config is explicit so permission, timeout, policy reference, and audit hashing never use implicit state."""
    _header("Stage 3: Kill Switch Transition - Apply Kill Switch Command (FR-RISK-043)")
    config, auth, kill_store, audit, approvals, inactive_state = _setup()

    command = create_kill_switch_command(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="operator safety stop",
        requested_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    result_state = unwrap_risk_response(
        apply_kill_switch_command(
            command,
            inactive_state,
            auth,
            approvals,
            audit,
            kill_store,
            config,
            now=NOW,
        ),
        operation="apply_kill_switch_command",
    )
    print(_format_result(result_state))
    print(
        f"Data -> state_id='{result_state.state_id}', state='{result_state.state}', version={result_state.version}"
    )


def fr_risk_044() -> None:
    """FR-RISK-044: Stage 3 — Return deterministic block/recovery eligibility; active or unknown applicable state blocks live risk increase, and recovery requires all applicable scopes inactive plus Trading reconciliation. Config and authenticated trace context are required so the returned canonical decision contains no invented policy or trace identity."""
    _header("Stage 3: Kill Switch Check - Check Risk Kill Switch (FR-RISK-044)")
    config, auth, _, _, _, inactive_state = _setup()

    decision_package = unwrap_risk_response(
        check_risk_kill_switch(
            (inactive_state,),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            auth,
            reconciled=True,
            now=NOW,
        ),
        operation="check_risk_kill_switch",
    )
    print(_format_result(decision_package))
    print(
        f"Data -> decision_id='{decision_package.decision_id}', state='{decision_package.state.value}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-13 — kill_switch/ — Risk Kill-Switch State Governance\n\n"
        "Purpose: Authorize kill-switch activation/clearance and evaluate block/recovery eligibility under strict precedence.\n\n"
        "Module flow:\n"
        "-> Stage 1: Build untrusted kill-switch command, current state, auth context, and clearance attestation\n"
        "-> Stage 2: Validate permissions, distinct dual-principal clearance, and scope precedence\n"
        "-> Stage 3: Return updated KillSwitchState or RiskDecisionPackage block check"
    )
    fr_risk_043()
    fr_risk_044()


if __name__ == "__main__":
    main()
