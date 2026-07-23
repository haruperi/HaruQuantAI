"""Workflow integration test for advisory Risk scenario analysis."""

from decimal import Decimal

from app.services.risk.contracts import ScenarioDefinition
from app.services.risk.scenarios import run_risk_scenario_analysis

from tests.risk import _support as examples


def test_scenario_analysis_is_deterministic_and_advisory() -> None:
    """Produce reproducible differences without approval or input mutation."""
    config = examples._config()
    snapshot = examples._snapshot(config)
    before = snapshot.model_dump(mode="python")
    scenario = ScenarioDefinition(
        scenario_id="combined-stress",
        shocks={
            "equity": Decimal("-0.15"),
            "portfolio_correlation": Decimal("0.30"),
        },
        randomized=False,
        seed=None,
        assumptions=("declared aggregate stress",),
    )
    first = run_risk_scenario_analysis(snapshot, (scenario,), config, now=examples.NOW)
    second = run_risk_scenario_analysis(snapshot, (scenario,), config, now=examples.NOW)
    assert first == second
    assert first[0].advisory_only is True
    assert first[0].approved is False
    assert snapshot.model_dump(mode="python") == before
