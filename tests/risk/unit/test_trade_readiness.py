"""Unit tests for the fixed-precedence submit-time trade readiness gate."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.risk.contracts import KillSwitchState, LimitStatus
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.governor import evaluate_trade_readiness
from app.services.risk.stop_validation import build_stop_validation

from tests.risk.unit.test_limits import _config, _market, _snapshot

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _stop_validation() -> dict[str, object]:
    """Build one bounded valid BUY stop-validation mapping."""
    return build_stop_validation(
        symbol="EURUSD",
        side="BUY",
        entry_price=Decimal("1.1000"),
        stop_price=Decimal("1.0950"),
        tick_size=Decimal("0.0001"),
        min_stop_distance=Decimal("0.0020"),
        contract_value=Decimal(100000),
        quantity=Decimal("0.1"),
        evaluated_at=NOW,
    )


def test_readiness_gate_composes_every_check_in_order() -> None:
    """Compose market, lock, stop, portfolio, and stress checks in order."""
    config = _config(live=True)
    snapshot = _snapshot(config).model_copy(
        update={
            "drawdown": Decimal("0.01"),
            "margin_utilization": Decimal("0.1"),
            "daily_loss": Decimal(0),
            "total_loss": Decimal(0),
        }
    )
    results = unwrap_risk_response(
        evaluate_trade_readiness(
            _stop_validation(),
            (),
            {},
            snapshot,
            _market(),
            config,
            {"nominal": Decimal("0.01")},
            Decimal("0.10"),
            now=NOW,
        ),
        operation="evaluate_trade_readiness",
    )
    limit_ids = [item.limit_id for item in results]
    assert "lock" in limit_ids
    assert "stop_side" in limit_ids
    assert "drawdown_state" in limit_ids
    assert "stress_loss_gate" in limit_ids
    assert [item.precedence for item in results] == list(range(len(results)))


def test_readiness_gate_blocks_on_active_new_exposure_lock() -> None:
    """Block the lock check when a full activation is applicable."""
    config = _config(live=True)
    snapshot = _snapshot(config).model_copy(
        update={
            "drawdown": Decimal("0.01"),
            "margin_utilization": Decimal("0.1"),
            "daily_loss": Decimal(0),
            "total_loss": Decimal(0),
        }
    )
    active = KillSwitchState(
        state_id="global-state-1",
        scope_level="global",
        scope={},
        state="active",
        reason="operator safety stop",
        version=1,
        updated_at=NOW,
    )
    results = unwrap_risk_response(
        evaluate_trade_readiness(
            _stop_validation(),
            (active,),
            {},
            snapshot,
            _market(),
            config,
            {"nominal": Decimal("0.01")},
            Decimal("0.10"),
            now=NOW,
        ),
        operation="evaluate_trade_readiness",
    )
    lock_result = next(item for item in results if item.limit_id == "lock")
    assert lock_result.status is LimitStatus.BLOCKED
