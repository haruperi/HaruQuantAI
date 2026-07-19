"""Unit tests for migration-evidenced position sizing formulas."""

from decimal import Decimal

import pytest
from app.services.risk.config import RiskConfig
from app.services.risk.contracts import (
    PortfolioRiskSnapshot,
    PositionSizingRequest,
    RiskDomainError,
    RiskErrorCode,
)
from app.services.risk.portfolio import build_portfolio_risk_snapshot
from app.services.risk.sizing import calculate_position_size

from tests.risk.unit.test_snapshot import _config, _state


def _snapshot() -> PortfolioRiskSnapshot:
    """Build one canonical portfolio snapshot for sizing tests."""
    return build_portfolio_risk_snapshot(_state(), _config(), now=_state().as_of)


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
        "request_id": "request-1",
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
    snapshot = build_portfolio_risk_snapshot(_state(), _config(), now=_state().as_of)
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
        result = calculate_position_size(_request(method), snapshot, config)
        assert result.normalized_size == expected_size
        assert not result.approved
    too_small_values = _request("fixed_lot").model_dump()
    too_small_values["fixed_lot"] = Decimal("0.001")
    too_small = PositionSizingRequest.model_validate(too_small_values)
    result = calculate_position_size(too_small, snapshot, _config())
    assert result.normalized_size == Decimal(0)
    assert result.normalized_size != Decimal("0.1")


def test_fixed_fractional_out_of_range_fraction_fails_closed() -> None:
    """A contract-valid but >1 fixed fraction fails inside the calculator."""
    request = _request_with("fixed_fractional", risk_fraction=Decimal(2))
    with pytest.raises(RiskDomainError) as exc:
        calculate_position_size(request, _snapshot(), _config())
    assert exc.value.code == RiskErrorCode.CALCULATION_FAILED


def test_kelly_insufficient_trades_rejects_without_fallback() -> None:
    """Too few Kelly trades reject when fallback is not configured."""
    request = _request_with("fractional_kelly", trade_count=5)
    with pytest.raises(RiskDomainError) as exc:
        calculate_position_size(request, _snapshot(), _kelly_config())
    assert exc.value.code == RiskErrorCode.INSUFFICIENT_K_EVIDENCE


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
    result = calculate_position_size(request, _snapshot(), config)
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
    with pytest.raises(RiskDomainError) as exc:
        calculate_position_size(_request("fractional_kelly"), _snapshot(), config)
    assert exc.value.code == RiskErrorCode.CALCULATION_FAILED


def test_volatility_out_of_range_fraction_fails_closed() -> None:
    """A contract-valid but >1 volatility fraction fails inside the calculator."""
    request = _request_with("volatility", risk_fraction=Decimal(2))
    with pytest.raises(RiskDomainError) as exc:
        calculate_position_size(request, _snapshot(), _config())
    assert exc.value.code == RiskErrorCode.INSUFFICIENT_VOLATILITY_EVIDENCE


def test_correlation_penalty_applied_when_breached() -> None:
    """A configured penalty scales size and is disclosed on breach."""
    config = _config().model_copy(update={"correlation_size_penalty": Decimal("0.5")})
    snapshot = _snapshot().model_copy(update={"portfolio_correlation": Decimal("0.90")})
    result = calculate_position_size(_request("fixed_lot"), snapshot, config)
    assert result.correlation_adjustment == Decimal("0.5")
    assert "correlation_size_penalty" in result.constraints_applied
    assert result.normalized_size == Decimal("0.5")


def test_correlation_penalty_missing_evidence_fails_closed() -> None:
    """A configured penalty without correlation evidence fails closed."""
    config = _config().model_copy(update={"correlation_size_penalty": Decimal("0.5")})
    snapshot = _snapshot().model_copy(update={"portfolio_correlation": None})
    with pytest.raises(RiskDomainError) as exc:
        calculate_position_size(_request("fixed_lot"), snapshot, config)
    assert exc.value.code == RiskErrorCode.MISSING_EVIDENCE


def test_broker_maximum_cap_is_disclosed() -> None:
    """A raw size above the broker maximum is capped and disclosed."""
    request = _request_with("fixed_lot", fixed_lot=Decimal(1000))
    result = calculate_position_size(request, _snapshot(), _config())
    assert result.normalized_size == Decimal(100)
    assert "broker_maximum_cap" in result.constraints_applied


def test_broker_step_floor_is_disclosed() -> None:
    """A raw size off the broker step grid is floored and disclosed."""
    request = _request_with(
        "fixed_lot", fixed_lot=Decimal("1.005"), broker_size_step=Decimal("0.01")
    )
    result = calculate_position_size(request, _snapshot(), _config())
    assert result.normalized_size == Decimal("1.00")
    assert "broker_step_floor" in result.constraints_applied
