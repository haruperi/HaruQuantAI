"""Integration tests for API package-root compatibility with Risk contracts."""

from datetime import UTC, datetime, timedelta

from app.services.risk import (
    create_approval_attestation,
    create_kill_switch_command,
    create_kill_switch_state,
)


def test_api_consumes_risk_command_and_attestation_contracts() -> None:
    """Verify API package-root acceptance of Risk command and attestation contracts."""
    now = datetime.now(UTC)

    cmd = create_kill_switch_command(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="emergency manual trip",
        requested_at=now,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    assert cmd.action == "activate"
    assert cmd.scope_level == "global"
    assert cmd.contract_version == "v1"
    assert cmd.schema_id == "risk.kill_switch_command.v1"

    att = create_approval_attestation(
        attestation_id="att-1",
        principal_id="admin-2",
        action="kill_switch:clear",
        scope={"scope": "global"},
        policy_ref="policy-ref-1",
        policy_version="v1",
        issued_at=now,
        expires_at=now + timedelta(minutes=15),
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    assert att.principal_id == "admin-2"
    assert att.contract_version == "v1"
    assert att.schema_id == "risk.approval_attestation.v1"

    ks = create_kill_switch_state(
        state_id="ks-1",
        scope_level="global",
        scope={"scope": "global"},
        state="active",
        version=2,
        reason="emergency manual trip",
        updated_at=now,
    )
    assert ks.state == "active"
    assert ks.contract_version == "v1"
    assert ks.schema_id == "risk.kill_switch_state.v1"


def test_api_rejects_incompatible_risk_contract_version() -> None:
    """Verify that API rejects Risk commands with incompatible schema versions or shapes."""
    import pytest
    from pydantic import ValidationError

    raw_invalid = {
        "contract_version": "v2",  # Incompatible version
        "action": "activate",
        "scope_level": "global",
        "reason": "emergency manual trip",
        "requested_at": datetime.now(UTC).isoformat(),
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
    }
    with pytest.raises(ValidationError):
        create_kill_switch_command(**raw_invalid)
