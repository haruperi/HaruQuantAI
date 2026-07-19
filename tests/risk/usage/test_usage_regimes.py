"""Runnable usage example for public Risk regime assessment."""

from app.services.risk.regimes import assess_risk_regime

from tests.risk.usage import test_usage_policy as examples


def test_usage_assessment_regime() -> None:
    """Classify supplied portfolio and market evidence with configured thresholds."""
    config = examples._config().model_copy(update={"regime_assessment_enabled": True})
    assessment = assess_risk_regime(
        examples._snapshot(config),
        examples._market(),
        config,
        now=examples.NOW,
    )
    assert assessment.states["volatility"] == "normal"
    assert assessment.modifiers == {}
