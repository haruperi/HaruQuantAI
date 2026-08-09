"""Unit tests for migration-evidenced position sizing formulas."""

from decimal import Decimal

import pytest
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import (
    PortfolioRiskSnapshot,
    PositionSizingRequest,
    RiskErrorCode,
)
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.portfolio import build_portfolio_risk_snapshot
from app.services.risk.sizing import (
    calculate_planned_risk_reward,
    calculate_position_size,
)

from tests.risk.unit.test_snapshot import _config, _state


def _snapshot() -> PortfolioRiskSnapshot:
    """Build one canonical portfolio snapshot for sizing tests."""
    return unwrap_risk_response(
        build_portfolio_risk_snapshot(_state(), _config(), now=_state().as_of),
        operation="build_portfolio_risk_snapshot",
    )


def _request_with(method: str, **overrides: object) -> PositionSizingRequest:
    """Build a sizing request for one method with explicit field overrides."""
    values = _request(method).model_dump()
    values.update(overrides)
    return PositionSizingRequest.model_validate(values)


def _request(method: str) -> PositionSizingRequest:
    """Build complete evidence for one selected sizing method."""
    values: dict[str, object] = {
        "method": method,
        "requested_size": Decimal(1),
        "fixed_lot": None,
        "risk_amount": None,
        "risk_fraction": None,
        "stop_distance": None,
        "unit_value": None,
        "milestone_multiplier": None,
        "win_rate": None,
        "payoff_ratio": None,
        "trade_count": None,
        "volatility_multiplier": None,
        "asset_volatility": None,
        "broker_min_size": Decimal("0.01"),
        "broker_max_size": Decimal(100),
        "broker_size_step": Decimal("0.01"),
        "evidence_refs": {"snapshot": "snapshot-1"},
        "request_id": "req-11111111-1111-4111-8111-111111111111",
    }
    if method == "fixed_lot":
        values["fixed_lot"] = Decimal(1)
    elif method == "fixed_risk":
        values.update(
            risk_amount=Decimal(1000),
            stop_distance=Decimal(100),
            unit_value=Decimal(10),
        )
    elif method == "fixed_fractional":
        values.update(
            risk_fraction=Decimal("0.10"),
            stop_distance=Decimal(100),
            unit_value=Decimal(10),
        )
    elif method == "milestone":
        values.update(fixed_lot=Decimal("0.5"), milestone_multiplier=Decimal(2))
    elif method == "fractional_kelly":
        values.update(
            win_rate=Decimal("0.60"),
            payoff_ratio=Decimal(2),
            trade_count=30,
            stop_distance=Decimal(100),
            unit_value=Decimal(10),
        )
    elif method == "volatility":
        values.update(
            risk_fraction=Decimal("0.10"),
            volatility_multiplier=Decimal(2),
            asset_volatility=Decimal(50),
            unit_value=Decimal(10),
        )
    return PositionSizingRequest.model_validate(values)


def _kelly_config() -> RiskConfig:
    """Build policy enabling bounded half-Kelly sizing."""
    return _config().model_copy(
        update={
            "fractional_kelly_multiplier": Decimal("0.5"),
            "kelly_insufficient_evidence_mode": "reject",
        }
    )


def test_all_six_methods_and_no_point_one_fallback() -> None:
    """Retain all formulas and return zero below the broker minimum."""
    snapshot = _snapshot()
    expected = {
        "fixed_lot": Decimal(1),
        "fixed_risk": Decimal(1),
        "fixed_fractional": Decimal(1),
        "milestone": Decimal(1),
        "fractional_kelly": Decimal(2),
        "volatility": Decimal(1),
    }
    for method, expected_size in expected.items():
        config = _kelly_config() if method == "fractional_kelly" else _config()
        result = unwrap_risk_response(
            calculate_position_size(_request(method), snapshot, config),
            operation="calculate_position_size",
        )
        assert result.normalized_size == expected_size
        assert not result.approved
    too_small_values = _request("fixed_lot").model_dump()
    too_small_values["fixed_lot"] = Decimal("0.001")
    too_small = PositionSizingRequest.model_validate(too_small_values)
    result = unwrap_risk_response(
        calculate_position_size(too_small, snapshot, _config()),
        operation="calculate_position_size",
    )
    assert result.normalized_size == Decimal(0)
    assert result.normalized_size != Decimal("0.1")


def test_fixed_fractional_out_of_range_fraction_fails_closed() -> None:
    """A contract-valid but >1 fixed fraction fails inside the calculator."""
    request = _request_with("fixed_fractional", risk_fraction=Decimal(2))
    response = calculate_position_size(request, _snapshot(), _config())
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.CALCULATION_FAILED.value


def test_kelly_insufficient_trades_rejects_without_fallback() -> None:
    """Too few Kelly trades reject when fallback is not configured."""
    request = _request_with("fractional_kelly", trade_count=5)
    response = calculate_position_size(request, _snapshot(), _kelly_config())
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.INSUFFICIENT_K_EVIDENCE.value


def test_kelly_insufficient_trades_uses_fixed_risk_fallback() -> None:
    """Configured fallback sizes from complete fixed-risk evidence."""
    config = _config().model_copy(
        update={
            "fractional_kelly_multiplier": Decimal("0.5"),
            "kelly_insufficient_evidence_mode": "fixed_risk_fallback",
        }
    )
    request = _request_with(
        "fractional_kelly", trade_count=5, risk_amount=Decimal(1000)
    )
    result = unwrap_risk_response(
        calculate_position_size(request, _snapshot(), config),
        operation="calculate_position_size",
    )
    assert result.fallback_used
    assert result.fallback_reason == "insufficient_k_evidence"
    assert not result.approved


def test_full_kelly_requires_explicit_waiver() -> None:
    """A full-Kelly multiplier without an approved waiver fails closed."""
    config = _config().model_copy(
        update={
            "fractional_kelly_multiplier": Decimal(1),
            "kelly_insufficient_evidence_mode": "reject",
            "allow_full_kelly": False,
        }
    )
    response = calculate_position_size(
        _request("fractional_kelly"), _snapshot(), config
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.CALCULATION_FAILED.value


def test_volatility_out_of_range_fraction_fails_closed() -> None:
    """A contract-valid but >1 volatility fraction fails inside the calculator."""
    request = _request_with("volatility", risk_fraction=Decimal(2))
    response = calculate_position_size(request, _snapshot(), _config())
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.INSUFFICIENT_VOLATILITY_EVIDENCE.value


def test_correlation_penalty_applied_when_breached() -> None:
    """A configured penalty scales size and is disclosed on breach."""
    config = _config().model_copy(update={"correlation_size_penalty": Decimal("0.5")})
    snapshot = _snapshot().model_copy(update={"portfolio_correlation": Decimal("0.90")})
    result = unwrap_risk_response(
        calculate_position_size(_request("fixed_lot"), snapshot, config),
        operation="calculate_position_size",
    )
    assert result.correlation_adjustment == Decimal("0.5")
    assert "correlation_size_penalty" in result.constraints_applied
    assert result.normalized_size == Decimal("0.5")


def test_correlation_penalty_missing_evidence_fails_closed() -> None:
    """A configured penalty without correlation evidence fails closed."""
    config = _config().model_copy(update={"correlation_size_penalty": Decimal("0.5")})
    snapshot = _snapshot().model_copy(update={"portfolio_correlation": None})
    response = calculate_position_size(_request("fixed_lot"), snapshot, config)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.MISSING_EVIDENCE.value


def test_broker_maximum_cap_is_disclosed() -> None:
    """A raw size above the broker maximum is capped and disclosed."""
    request = _request_with("fixed_lot", fixed_lot=Decimal(1000))
    result = unwrap_risk_response(
        calculate_position_size(request, _snapshot(), _config()),
        operation="calculate_position_size",
    )
    assert result.normalized_size == Decimal(100)
    assert "broker_maximum_cap" in result.constraints_applied


def test_broker_step_floor_is_disclosed() -> None:
    """A raw size off the broker step grid is floored and disclosed."""
    request = _request_with(
        "fixed_lot", fixed_lot=Decimal("1.005"), broker_size_step=Decimal("0.01")
    )
    result = unwrap_risk_response(
        calculate_position_size(request, _snapshot(), _config()),
        operation="calculate_position_size",
    )
    assert result.normalized_size == Decimal("1.00")
    assert "broker_step_floor" in result.constraints_applied


def test_additional_cap_binds_tighter_than_broker_maximum() -> None:
    """The strictest of the broker cap and every named cap applies."""
    request = _request_with("fixed_lot", fixed_lot=Decimal(50))
    result = unwrap_risk_response(
        calculate_position_size(
            request,
            _snapshot(),
            _config(),
            additional_caps={"margin": Decimal(2), "symbol": None},
        ),
        operation="calculate_position_size",
    )
    assert result.normalized_size == Decimal(2)
    assert "margin_cap" in result.constraints_applied


@pytest.mark.parametrize(
    ("raw", "caps"),
    [
        (Decimal(1000), {"risk": Decimal(30)}),
        (Decimal(1000), {"margin": Decimal(5), "symbol": Decimal(40)}),
        (Decimal(1000), {"portfolio": Decimal(0), "liquidity": Decimal(90)}),
        (Decimal(1000), {}),
        (Decimal("0.5"), {"strategy": Decimal(60)}),
    ],
)
def test_normalized_size_never_exceeds_any_supplied_cap(
    raw: Decimal, caps: dict[str, Decimal]
) -> None:
    """Property: the normalized size never exceeds any individual cap."""
    request = _request_with("fixed_lot", fixed_lot=raw)
    result = unwrap_risk_response(
        calculate_position_size(request, _snapshot(), _config(), additional_caps=caps),
        operation="calculate_position_size",
    )
    assert result.normalized_size <= request.broker_max_size
    for value in caps.values():
        if value is not None:
            assert result.normalized_size <= value


def test_planned_risk_reward_calculates_ratio() -> None:
    """Calculate planned risk, reward, and their ratio from bounded distances."""
    result = unwrap_risk_response(
        calculate_planned_risk_reward(
            stop_distance=Decimal(10),
            target_distance=Decimal(30),
            contract_value=Decimal(10),
            quantity=Decimal(1),
            fees=Decimal(5),
        ),
        operation="calculate_planned_risk_reward",
    )
    assert result["planned_risk"] == Decimal(105)
    assert result["planned_reward"] == Decimal(300)
    assert result["reward_risk_ratio"] == Decimal(300) / Decimal(105)


def test_planned_risk_reward_rejects_non_positive_distance() -> None:
    """Reject a non-positive stop distance."""
    response = calculate_planned_risk_reward(
        stop_distance=Decimal(0),
        target_distance=Decimal(30),
        contract_value=Decimal(10),
        quantity=Decimal(1),
    )
    assert response.status == "error"
