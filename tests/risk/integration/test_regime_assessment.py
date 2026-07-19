"""Workflow integration test for supplied-evidence Risk regime assessment."""

from decimal import Decimal

from app.services.risk.regimes import assess_risk_regime

from tests.risk.usage import test_usage_policy as examples


def test_regime_assessment_workflow_end_to_end() -> None:
    """Classify mixed risk states and preserve deterministic transition evidence."""
    config = examples._config().model_copy(update={"regime_assessment_enabled": True})
    market = examples._market().model_copy(update={"volatility": Decimal("0.03")})
    assessment = assess_risk_regime(
        examples._snapshot(config), market, config, now=examples.NOW
    )
    assert assessment.states["volatility"] == "elevated"
    assert assessment.modifiers["volatility"] == Decimal("0.75")
    assert "volatility:unknown->elevated" in assessment.transitions
