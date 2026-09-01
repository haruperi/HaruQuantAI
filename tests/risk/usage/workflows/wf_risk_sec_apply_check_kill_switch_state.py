"""WF-RISK-SEC: apply and check canonical kill-switch state."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.kernel.serialization import canonical_json
from app.services.risk import (
    apply_kill_switch_command,
    check_risk_kill_switch,
    create_kill_switch_command,
    create_risk_audit_chain,
)
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-SEC"
STAGES = (
    "Accept explicit scoped create_kill_switch_command plus separate create_auth_context.",
    "Validate precedence, authorization, and transition requirements.",
    "Persist canonical state, revoke affected approvals, and seal audit evidence.",
    "Check the complete hierarchy for deterministic block/recovery truth.",
    "Return create_kill_switch_state and Risk decision without mutating execution controls.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: UI/API submits explicit authorized activation.
    _stage(1)
    config = examples._config()
    _, approvals, _ = examples._services(config)
    store = examples._KillStore()
    audit = create_risk_audit_chain(config, store, lambda: examples.NOW, canonical_json)
    command = create_kill_switch_command(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="operator safety stop",
        requested_at=examples.NOW,
        request_id=examples.REQUEST_ID,
        workflow_id=examples.WORKFLOW_ID,
        correlation_id=examples.CORRELATION_ID,
    )
    print("Input:", command.action, command.scope_level)
    # Stage 2: Validate state transition and authority.
    _stage(2)
    print("Principal:", examples._auth(config).principal_id)
    # Stage 3: Apply through the Risk-owned mutation boundary.
    _stage(3)
    active = unwrap_risk_response(
        apply_kill_switch_command(
            command,
            examples._inactive_state(),
            examples._auth(config),
            approvals,
            audit,
            store,
            config,
            now=examples.NOW,
        ),
        operation="apply_kill_switch_command",
    )
    print("Persisted state:", active.state)
    # Stage 4: Check applicable hierarchy.
    _stage(4)
    decision = unwrap_risk_response(
        check_risk_kill_switch(
            (active,),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            examples._auth(config),
            reconciled=False,
            now=examples.NOW,
        ),
        operation="check_risk_kill_switch",
    )
    print("Decision:", decision.state)
    # Stage 5 — OUTPUT BOUNDARY: Return canonical state/decision; execution untouched.
    _stage(5)
    print("Output:", type(active).__name__, type(decision).__name__)


if __name__ == "__main__":
    main()
