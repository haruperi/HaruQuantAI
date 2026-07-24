"""Standalone UI/API operator-route usage."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api.identity import require_auth_context
from app.services.api.routes import operator, operator_router
from app.services.risk import (
    ApprovalAttestation,
    KillSwitchCommand,
    KillSwitchState,
)
from app.utils import AuthContext
from fastapi import FastAPI
from tests.api._support import post_json

NOW = datetime(2026, 7, 24, 9, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


def _auth() -> AuthContext:
    """Build one authorized human operator.

    Returns:
        Valid authenticated context.
    """
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="operator-example",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("risk.kill.activate",),
        scopes=("risk",),
        tenant_or_environment="simulation",
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        issued_at=NOW,
    )


def fr_api_034() -> dict[str, object]:
    """FR-API-034: Authenticate/authorize a human operator; construct
    KillSwitchCommand v1 with explicit global/portfolio/strategy/symbol scope and
    applicable identifiers; submit activation immediately with the commanding
    principal's separate AuthContext; for clearance require and submit a matching
    current ApprovalAttestation v1 issued by a different authorized principal;
    reject same-principal clearance before delegation while Risk remains
    authoritative; and expose protected readiness/OperationalEvent v1 views plus
    bounded Data-owned audit pages without issuing Risk tokens, policy verdicts,
    or direct store access.

    Returns:
        JSON activation response from the complete HTTP boundary.
    """
    commands: list[KillSwitchCommand] = []

    def transition(
        command: KillSwitchCommand,
        auth: AuthContext,
        attestation: ApprovalAttestation | None,
    ) -> KillSwitchState:
        """Demonstrate delegation to an injected Risk-owned boundary."""
        assert auth.principal_id == "operator-example"
        assert attestation is None
        commands.append(command)
        return KillSwitchState(
            state_id="global-active-example",
            scope_level="global",
            scope={},
            state="active",
            reason=command.reason,
            version=2,
            updated_at=NOW,
        )

    def sink(value: object, *, idempotency_key: str) -> None:
        """Accept one bounded channel-neutral example alert."""
        del value
        assert len(idempotency_key) == 64

    app = FastAPI()
    app.include_router(operator_router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[operator._kill_switch_transition] = lambda: transition
    app.dependency_overrides[operator._critical_alert_sink] = lambda: sink
    status_code, body = post_json(
        app,
        "/api/operator/kill-switch",
        {
            "action": "activate",
            "scope_level": "global",
            "portfolio_id": None,
            "strategy_id": None,
            "symbol": None,
            "reason": "operator safety stop",
            "requested_at": NOW.isoformat(),
            "attestation": None,
        },
    )
    assert status_code == 200
    assert len(commands) == 1
    return body


def main() -> None:
    """Run the operator-route requirement demonstration."""
    result = fr_api_034()
    state = result["state"]
    delivery = result["delivery"]
    assert isinstance(state, dict)
    assert isinstance(delivery, dict)
    print(
        {
            "state": state["state"],
            "delivery": delivery["status"],
        }
    )


if __name__ == "__main__":
    main()
