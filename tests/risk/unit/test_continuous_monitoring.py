"""Unit tests for the continuous-monitoring recalculation classifier."""

from datetime import UTC, datetime, timedelta

from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.validity import requires_risk_recalculation

from tests.risk.unit.test_limits import _config

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_recalculation_required_when_group_not_configured() -> None:
    """Fail closed to recalculation when no assessment group is configured."""
    config = _config()
    result = unwrap_risk_response(
        requires_risk_recalculation(
            "fill", last_evaluated_at=NOW, config=config, now=NOW
        ),
        operation="requires_risk_recalculation",
    )
    assert result is True


def test_recalculation_required_for_registered_event() -> None:
    """Require recalculation immediately for a registered triggering event."""
    config = _config(live=True)
    result = unwrap_risk_response(
        requires_risk_recalculation(
            "fill", last_evaluated_at=NOW, config=config, now=NOW
        ),
        operation="requires_risk_recalculation",
    )
    assert result is True


def test_recalculation_not_required_within_staleness_bound() -> None:
    """Skip recalculation for an unregistered event within the staleness bound."""
    config = _config(live=True)
    result = unwrap_risk_response(
        requires_risk_recalculation(
            "unregistered_event",
            last_evaluated_at=NOW,
            config=config,
            now=NOW + timedelta(seconds=10),
        ),
        operation="requires_risk_recalculation",
    )
    assert result is False


def test_recalculation_required_once_staleness_bound_exceeded() -> None:
    """Require recalculation once the staleness bound is exceeded."""
    config = _config(live=True)
    result = unwrap_risk_response(
        requires_risk_recalculation(
            "unregistered_event",
            last_evaluated_at=NOW,
            config=config,
            now=NOW + timedelta(seconds=200),
        ),
        operation="requires_risk_recalculation",
    )
    assert result is True
