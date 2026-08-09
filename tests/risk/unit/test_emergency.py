"""Unit tests for the configured Risk emergency-state evaluator."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.risk.contracts import LimitStatus
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.governor import evaluate_emergency_state

from tests.risk.unit.test_limits import _config, _snapshot

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_emergency_state_disabled_without_configured_group() -> None:
    """Pass when no emergency rule group is configured."""
    config = _config()
    result = unwrap_risk_response(
        evaluate_emergency_state(_snapshot(config), config, now=NOW),
        operation="evaluate_emergency_state",
    )
    assert result.status is LimitStatus.PASS


def test_emergency_state_blocks_on_margin_call_utilization() -> None:
    """Block when margin utilization reaches the configured emergency threshold."""
    config = _config(live=True)
    snapshot = _snapshot(config).model_copy(
        update={"margin_utilization": Decimal("0.85"), "drawdown": Decimal("0.01")}
    )
    result = unwrap_risk_response(
        evaluate_emergency_state(snapshot, config, now=NOW),
        operation="evaluate_emergency_state",
    )
    assert result.status is LimitStatus.BLOCKED


def test_emergency_state_blocks_on_drawdown_breach() -> None:
    """Block when drawdown reaches or exceeds max_drawdown."""
    config = _config(live=True)
    snapshot = _snapshot(config).model_copy(
        update={"margin_utilization": Decimal("0.1"), "drawdown": Decimal("0.10")}
    )
    result = unwrap_risk_response(
        evaluate_emergency_state(snapshot, config, now=NOW),
        operation="evaluate_emergency_state",
    )
    assert result.status is LimitStatus.BLOCKED


def test_emergency_state_blocks_on_connectivity_staleness() -> None:
    """Block when evidence is staler than the configured connectivity bound."""
    config = _config(live=True)
    snapshot = _snapshot(config).model_copy(
        update={"margin_utilization": Decimal("0.1"), "drawdown": Decimal("0.01")}
    )
    result = unwrap_risk_response(
        evaluate_emergency_state(snapshot, config, now=NOW + timedelta(seconds=60)),
        operation="evaluate_emergency_state",
    )
    assert result.status is LimitStatus.BLOCKED


def test_emergency_state_passes_when_no_trigger_fires() -> None:
    """Pass when every configured emergency trigger stays within bounds."""
    config = _config(live=True)
    snapshot = _snapshot(config).model_copy(
        update={"margin_utilization": Decimal("0.1"), "drawdown": Decimal("0.01")}
    )
    result = unwrap_risk_response(
        evaluate_emergency_state(snapshot, config, now=NOW),
        operation="evaluate_emergency_state",
    )
    assert result.status is LimitStatus.PASS
