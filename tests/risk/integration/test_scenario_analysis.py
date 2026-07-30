"""Workflow integration test for advisory Risk scenario analysis."""

from decimal import Decimal

from app.services.risk import create_scenario_definition, run_risk_scenario_analysis

from tests.risk import _support as examples


def test_scenario_analysis_is_deterministic_and_advisory() -> None:
    """Produce reproducible differences without approval or input mutation."""
    config = examples._config()
    snapshot = examples._snapshot(config)
    before = snapshot.model_dump(warnings=False, mode="python")
    scenario = create_scenario_definition(
        scenario_id="combined-stress",
        shocks={
            "equity": Decimal("-0.15"),
            "portfolio_correlation": Decimal("0.30"),
        },
        randomized=False,
        seed=None,
        assumptions=("declared aggregate stress",),
    )
    first = examples.unwrap_risk_response(
        run_risk_scenario_analysis(snapshot, (scenario,), config, now=examples.NOW),
        operation="run_risk_scenario_analysis",
    )
    second = examples.unwrap_risk_response(
        run_risk_scenario_analysis(snapshot, (scenario,), config, now=examples.NOW),
        operation="run_risk_scenario_analysis",
    )
    assert first == second
    assert first[0].advisory_only is True
    assert first[0].approved is False
    assert snapshot.model_dump(warnings=False, mode="python") == before
