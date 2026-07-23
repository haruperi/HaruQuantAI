"""Executable Risk kill-switch usage example.

Demonstrates authorized kill-switch activation and canonical block-state checking.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk.approvals import ApprovalTokenService
from app.services.risk.audit import RiskAuditChain
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import (
    KillSwitchCommand,
    KillSwitchState,
    RiskApprovalToken,
    RiskAuditRecord,
)
from app.services.risk.kill_switch import (
    apply_kill_switch_command,
    check_risk_kill_switch,
)
from app.utils import AuthContext, canonical_json, generate_id

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


class _KillStore:
    """Version-exact canonical state adapter."""

    def __init__(self) -> None:
        self.state: KillSwitchState | None = None

    def compare_and_swap(
        self,
        state: KillSwitchState,
        *,
        expected_version: int,
        timeout_seconds: Decimal | None,
    ) -> bool:
        del timeout_seconds
        current = expected_version if self.state is None else self.state.version
        if current != expected_version:
            return False
        self.state = state
        return True


def example_kill_switch() -> None:
    """Demonstrate kill-switch state transitions and checks."""
    print("=" * 80)
    print("Risk Example 4: Kill Switch State Transitions")
    print("=" * 80)

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

    audit = RiskAuditChain(config, _AuditStore(), lambda: NOW, canonical_json)
    token_store = _TokenStore()
    approvals = ApprovalTokenService(
        config,
        token_store,
        audit,
        lambda: NOW,
        lambda _: b"example-risk-signing-key-material-32-bytes",
        lambda evidence: evidence.principal_id == "operator-1",
    )
    kill_store = _KillStore()

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
    result_state = apply_kill_switch_command(
        command,
        inactive_state,
        auth,
        approvals,
        audit,
        kill_store,
        config,
        now=NOW,
    )
    print(
        f"Activated kill switch state: {result_state.state}, "
        f"reason: {result_state.reason}"
    )

    # 2. Check kill switch status
    decision_package = check_risk_kill_switch(
        (inactive_state,),
        {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
        config,
        auth,
        reconciled=True,
        now=NOW,
    )
    print(f"Checked kill switch decision state: {decision_package.state.value}")


def main() -> None:
    """Run Risk decisions usage example."""
    example_kill_switch()


if __name__ == "__main__":
    main()
