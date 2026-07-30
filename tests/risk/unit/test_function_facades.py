"""Focused validation of function-only Risk construction facades."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest
from app.services import risk

NOW = datetime(2026, 7, 30, tzinfo=UTC)


def test_every_keyword_factory_executes_validation_boundary() -> None:
    """Exercise every public keyword-only contract factory fail closed."""
    factories = [
        getattr(risk, name)
        for name in risk.__all__
        if name.startswith("create_")
        and tuple(inspect.signature(getattr(risk, name)).parameters.values())
        and all(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in inspect.signature(getattr(risk, name)).parameters.values()
        )
    ]
    assert factories
    for factory in factories:
        with pytest.raises((TypeError, ValueError)):
            factory()


@pytest.mark.parametrize("value", ["missing", "APPROVE "])
def test_enum_getters_reject_unknown_values(value: str) -> None:
    """Reject unregistered enum names and untrimmed values."""
    with pytest.raises(ValueError, match="is not a valid"):
        risk.get_decision_state(value)
    with pytest.raises(ValueError, match="is not a valid"):
        risk.get_limit_status(value)
    with pytest.raises(ValueError, match="is not a valid"):
        risk.get_risk_error_code(value)
    with pytest.raises(ValueError, match="is not a valid"):
        risk.get_drawdown_mode(value)


def test_opaque_coordinator_facades_reject_forged_receivers() -> None:
    """Reject objects not created by Risk's opaque coordinator factories."""
    with pytest.raises(TypeError, match="create_risk_audit_chain"):
        risk.append_risk_audit_record(object(), object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="create_risk_audit_chain"):
        risk.append_risk_kill_switch_transition(
            object(),
            object(),
            object(),
            object(),
            expected_version=0,
        )  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="create_risk_audit_chain"):
        risk.verify_risk_audit_chain(object(), ())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="create_approval_token_service"):
        risk.issue_risk_approval_token(object(), object(), object(), now=NOW)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="create_approval_token_service"):
        risk.validate_risk_approval_token(
            object(),
            object(),
            object(),
            {},
            now=NOW,
        )  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="create_approval_token_service"):
        risk.revoke_risk_approval_scope(object(), {}, "reason", now=NOW)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="create_risk_governor"):
        risk.review_trade_risk(
            object(),
            object(),
            object(),
            object(),
            (),
            object(),
            object(),
            now=NOW,
        )  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="create_risk_governor"):
        risk.run_portfolio_risk_governor(
            object(),
            object(),
            object(),
            (),
            object(),
            object(),
            now=NOW,
        )  # type: ignore[arg-type]
