"""Runnable usage example for advisory Risk scenario analysis."""

from decimal import Decimal

from app.services.risk.contracts import ScenarioDefinition
from app.services.risk.scenarios import run_risk_scenario_analysis

from tests.risk.usage import test_usage_policy as examples


def test_usage_analysis_scenarios() -> None:
    """Compare an immutable baseline with one bounded advisory projection."""
    config = examples._config()
    results = run_risk_scenario_analysis(
        examples._snapshot(config),
        (
            ScenarioDefinition(
                scenario_id="equity-stress",
                shocks={"equity": Decimal("-0.10")},
                randomized=True,
                seed=42,
                assumptions=("declared ten-percent equity shock",),
            ),
        ),
        config,
        now=examples.NOW,
    )
    assert results[0].seed == 42
    assert results[0].approved is False
