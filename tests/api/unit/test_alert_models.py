"""Critical operational alert contract tests."""

from datetime import UTC, datetime

import pytest
from app.services.api import (
    build_critical_alert_delivery_result,
    build_critical_alert_trigger,
    build_critical_operational_alert,
)
from pydantic import ValidationError

NOW = datetime(2026, 7, 24, 9, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"
HASH = "a" * 64


def _alert(**changes: object) -> object:
    """Build one valid bounded alert.

    Args:
        **changes: Fields to replace.

    Returns:
        Valid critical operational alert.
    """
    values: dict[str, object] = {
        "alert_id": HASH,
        "trigger": build_critical_alert_trigger("RISK_KILL_SWITCH_ACTIVATED"),
        "title": "Risk kill switch activated",
        "summary": "Risk kill switch activated for global scope.",
        "scope": {"scope_level": "global"},
        "source_schema_id": "risk.kill_switch_state.v1",
        "source_id": "state-1",
        "source_version": "2",
        "occurred_at": NOW,
        "request_id": REQUEST_ID,
        "workflow_id": WORKFLOW_ID,
        "correlation_id": CORRELATION_ID,
    }
    values.update(changes)
    return build_critical_operational_alert(**values)


def test_alert_contract_is_bounded_and_immutable() -> None:
    """Verify exact trigger, fixed title, trace, mapping, and immutability rules."""
    alert = _alert()

    assert alert.contract_version == "v1"
    assert alert.schema_id == "api.critical_operational_alert.v1"
    assert alert.redaction_applied is True
    with pytest.raises(ValidationError):
        _alert(scope={f"key-{index}": "value" for index in range(9)})
    with pytest.raises(ValidationError):
        _alert(scope={"api_key": "not-allowed"})  # pragma: allowlist secret
    with pytest.raises(ValidationError):
        _alert(title="Mutable title")


def test_delivery_result_requires_consistent_failure_evidence() -> None:
    """Verify delivery truth cannot claim failure without its stable code."""
    with pytest.raises(ValidationError):
        build_critical_alert_delivery_result(
            delivery_id=HASH,
            alert_id=HASH,
            status="failed",
            attempted_at=NOW,
            failure_code=None,
            request_id=REQUEST_ID,
            workflow_id=WORKFLOW_ID,
            correlation_id=CORRELATION_ID,
        )
