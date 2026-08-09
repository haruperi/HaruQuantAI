"""Tests for risk-parameter sensitivity analysis (TC-IMP-OPT-05)."""

from decimal import Decimal

import pytest
from app.services.optimization import (
    evaluate_risk_sensitivity,
    get_risk_sensitivity_contract_version,
    summarize_drawdown_threshold_sensitivity,
)

_RISK_PROFILE: dict[str, object] = {
    "max_risk_per_trade_pct": Decimal("0.01"),
    "max_drawdown": Decimal("0.10"),
    "drawdown_caution_threshold": Decimal("0.03"),
    "drawdown_restricted_threshold": Decimal("0.06"),
    "drawdown_critical_threshold": Decimal("0.08"),
}
_OUTCOMES: dict[str, float] = {
    "0.005": 1.0,
    "0.010": 2.0,
    "0.015": 3.0,
}


def test_evaluate_risk_sensitivity_returns_observations() -> None:
    """Sensitivity yields per-variant observations and a finite spread."""
    result = evaluate_risk_sensitivity(
        risk_profile=_RISK_PROFILE,
        outcome_by_risk_per_trade=_OUTCOMES,
    )
    assert result["parameter"] == "max_risk_per_trade_pct"
    assert len(result["observations"]) == 4
    assert isinstance(result["outcome_spread"], float)
    assert "hard_drawdown_limit_preserved" in result["caveats"]


def test_evaluate_risk_sensitivity_rejects_missing_risk_field() -> None:
    """Missing max_risk_per_trade_pct is rejected."""
    with pytest.raises(ValueError, match="max_risk_per_trade_pct"):
        evaluate_risk_sensitivity(
            risk_profile={"max_drawdown": Decimal("0.10")},
            outcome_by_risk_per_trade=_OUTCOMES,
        )


def test_evaluate_risk_sensitivity_rejects_empty_outcomes() -> None:
    """Empty outcome evidence is rejected."""
    with pytest.raises(ValueError, match="outcome evidence"):
        evaluate_risk_sensitivity(
            risk_profile=_RISK_PROFILE,
            outcome_by_risk_per_trade={},
        )


def test_evaluate_risk_sensitivity_rejects_non_numeric_outcome() -> None:
    """Non-numeric outcome values are rejected with TypeError."""
    with pytest.raises(TypeError, match="finite numbers"):
        evaluate_risk_sensitivity(
            risk_profile=_RISK_PROFILE,
            outcome_by_risk_per_trade={"0.010": "high"},  # type: ignore[dict-item]
        )


def test_evaluate_risk_sensitivity_never_weakens_hard_limit() -> None:
    """A variant that would weaken the hard limit is rejected."""
    with pytest.raises(ValueError, match="weaken"):
        evaluate_risk_sensitivity(
            risk_profile={
                "max_risk_per_trade_pct": Decimal("0.01"),
                "max_drawdown": Decimal("0.001"),
            },
            outcome_by_risk_per_trade=_OUTCOMES,
            variants=(Decimal("0.50"),),
        )


def test_summarize_drawdown_threshold_ladder_ordered() -> None:
    """Ordered thresholds bounded by max_drawdown are summarized correctly."""
    result = summarize_drawdown_threshold_sensitivity(_RISK_PROFILE)
    assert result["hard_limit_preserved"] is True
    assert len(result["ordered_thresholds"]) == 3


def test_summarize_drawdown_rejects_unordered_thresholds() -> None:
    """Unordered thresholds are rejected."""
    profile = dict(_RISK_PROFILE)
    profile["drawdown_restricted_threshold"] = Decimal("0.02")
    with pytest.raises(ValueError, match="strictly ordered"):
        summarize_drawdown_threshold_sensitivity(profile)


def test_summarize_drawdown_rejects_breach_of_hard_limit() -> None:
    """A threshold breaching max_drawdown is rejected."""
    profile = dict(_RISK_PROFILE)
    profile["drawdown_critical_threshold"] = Decimal("0.15")
    with pytest.raises(ValueError, match="breaches"):
        summarize_drawdown_threshold_sensitivity(profile)


def test_risk_sensitivity_contract_version() -> None:
    """Contract version is canonical."""
    assert get_risk_sensitivity_contract_version() == "v1"
