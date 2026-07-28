"""Executable Risk kill-switch usage example.

Demonstrates authorized kill-switch activation and canonical block-state checking.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk import (
    ApprovalAttestation,
    ApprovalTokenService,
    KillSwitchCommand,
    KillSwitchState,
    RiskApprovalToken,
    RiskAuditChain,
    RiskAuditRecord,
    RiskConfig,
    apply_kill_switch_command,
    check_risk_kill_switch,
    compute_config_hash,
)
from app.utils import AuthContext, canonical_json, generate_id

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = generate_id("req")
WORKFLOW_ID = generate_id("wf")
CORRELATION_ID = generate_id("cor")


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
    """Single-process token store."""

    def __init__(self) -> None:
        self.tokens: dict[str, RiskApprovalToken] = {}
        self.consumed: set[str] = set()
        self.revoked: set[str] = set()

    def save_issued(
        self, token: RiskApprovalToken, *, timeout_seconds: Decimal | None
    ) -> str:
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
        self.state: KillSwitchState | None = None

    def compare_and_swap_with_audit(
        self,
        state: KillSwitchState,
        record: RiskAuditRecord,
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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_kill_switch() -> None:
    """Demonstrate kill-switch state transitions and checks."""
    _header("Demonstrate kill-switch state transitions and checks.")
    print("Risk Example 4: Kill Switch State Transitions")

    config = RiskConfig(
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

    auth = AuthContext(
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
    audit = RiskAuditChain(config, kill_store, lambda: NOW, canonical_json)
    token_store = _TokenStore()
    approvals = ApprovalTokenService(
        config,
        token_store,
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    inactive_state = KillSwitchState(
        state_id="global-state-1",
        scope_level="global",
        scope={},
        state="inactive",
        reason="normal operation",
        version=1,
        updated_at=NOW,
    )

    # 1. Activate kill switch
    command = KillSwitchCommand(
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
    print(
        f"Activated kill switch state: {result_state.state}, "
        f"reason: {result_state.reason}"
    )

    # 2. Clear only with a distinct-principal attestation.
    clear_request_id = generate_id("req")
    clear_workflow_id = generate_id("wf")
    clear_correlation_id = generate_id("cor")
    clear_auth = auth.model_copy(
        update={
            "request_id": clear_request_id,
            "workflow_id": clear_workflow_id,
            "correlation_id": clear_correlation_id,
        }
    )
    clear_command = KillSwitchCommand(
        action="clear",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="reconciled and independently approved",
        requested_at=NOW,
        request_id=clear_request_id,
        workflow_id=clear_workflow_id,
        correlation_id=clear_correlation_id,
    )
    attestation = ApprovalAttestation(
        attestation_id="clearance-attestation-1",
        principal_id="operator-2",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref=unwrap_risk_response(
            compute_config_hash(config), operation="compute_config_hash"
        ),
        policy_version=config.policy_version,
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=clear_request_id,
        workflow_id=clear_workflow_id,
        correlation_id=clear_correlation_id,
    )
    cleared_state = unwrap_risk_response(
        apply_kill_switch_command(
            clear_command,
            result_state,
            clear_auth,
            approvals,
            audit,
            kill_store,
            config,
            attestation=attestation,
            now=NOW,
        ),
        operation="apply_kill_switch_command",
    )
    print(f"Distinct-principal clearance state: {cleared_state.state}")

    # 3. Check kill switch status
    decision_package = unwrap_risk_response(
        check_risk_kill_switch(
            (cleared_state,),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            auth,
            reconciled=True,
            now=NOW,
        ),
        operation="check_risk_kill_switch",
    )
    print(f"Checked kill switch decision state: {decision_package.state.value}")


_DEMONSTRATED = False


def _demonstrate_once() -> None:
    """Run the bounded kill-switch demonstration once."""
    global _DEMONSTRATED  # noqa: PLW0603
    if not _DEMONSTRATED:
        example_kill_switch()
        _DEMONSTRATED = True


def fr_risk_043() -> None:
    """FR-RISK-043: Apply an authorized, version-checked activation/clearance
    under `global > portfolio > strategy > symbol` precedence, atomically
    compare-and-swap canonical state with its Risk audit record in the injected
    store, revoke affected approvals on activation, and never mutate execution
    controls. Activation requires one authorized `AuthContext` and remains
    immediate and unilateral. Clearance additionally requires a matching current
    `ApprovalAttestation v1` from a different authorized principal; same-principal
    clearance leaves the active state unchanged and fails deterministically.
    Active config is explicit so permission, timeout, policy reference, and audit
    hashing never use implicit state."""
    _header(
        "FR-RISK-043: Apply an authorized, version-checked activation/clearance under `global > portfolio > strategy > symbol` precedence, atomically compare-and-swap canonical state with its Risk audit record in the injected store, revoke affected approvals on activation, and never mutate execution controls. Activation requires one authorized `AuthContext` and remains immediate and unilateral. Clearance additionally requires a matching current `ApprovalAttestation v1` from a different authorized principal; same-principal clearance leaves the active state unchanged and fails deterministically. Active config is explicit so permission, timeout, policy reference, and audit hashing never use implicit state."
    )
    _demonstrate_once()


def fr_risk_044() -> None:
    """FR-RISK-044: Return deterministic block/recovery eligibility; active or
    unknown applicable state blocks live risk increase, and recovery requires
    all applicable scopes inactive plus Trading reconciliation. Config and
    authenticated trace context are required so the returned canonical decision
    contains no invented policy or trace identity."""
    _header(
        "FR-RISK-044: Return deterministic block/recovery eligibility; active or unknown applicable state blocks live risk increase, and recovery requires all applicable scopes inactive plus Trading reconciliation. Config and authenticated trace context are required so the returned canonical decision contains no invented policy or trace identity."
    )
    _demonstrate_once()


def main() -> None:
    """Run every functional-requirement demonstration for the kill switch."""
    for demonstrate in (fr_risk_043, fr_risk_044):
        demonstrate()


if __name__ == "__main__":
    main()
