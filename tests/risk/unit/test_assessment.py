"""Unit tests for deterministic Risk regime assessment."""

from decimal import Decimal

from app.services.risk.config import RiskConfig
from app.services.risk.regimes import assess_risk_regime

from tests.risk import _support as examples


def _enabled_config() -> RiskConfig:
    """Build a validated enabled simulation regime policy."""
    return examples._config().model_copy(update={"regime_assessment_enabled": True})


def test_high_risk_modifiers_only_tighten() -> None:
    """Classify high supplied evidence and emit only stricter multipliers."""
    config = _enabled_config()
    market = examples._market().model_copy(
        update={
            "session_state": "closed",
            "calendar_state": "event",
            "liquidity": Decimal(0),
            "volatility": Decimal("0.05"),
            "correlations": {"EURUSD|USDJPY": Decimal("0.80")},
            "crisis_flags": ("market_dislocation",),
        }
    )
    snapshot = examples._snapshot(config).model_copy(
        update={
            "drawdown": Decimal("0.11"),
            "portfolio_correlation": Decimal("0.80"),
        }
    )
    assessment = assess_risk_regime(snapshot, market, config, now=examples.NOW)
    assert set(assessment.states.values()) == {"high"}
    assert set(assessment.modifiers.values()) == {Decimal("0.50")}
    assert all(
        Decimal(0) < value <= Decimal(1) for value in assessment.modifiers.values()
    )
    assert len(assessment.transitions) == 7


def test_disabled_assessment_is_explicit() -> None:
    """Return explicit unknown states and no modifier when disabled."""
    config = examples._config()
    assessment = assess_risk_regime(
        examples._snapshot(config),
        examples._market(),
        config,
        now=examples.NOW,
    )
    assert set(assessment.states.values()) == {"unknown"}
    assert assessment.modifiers == {}
    assert assessment.missing_fields == ("assessment_disabled",)
