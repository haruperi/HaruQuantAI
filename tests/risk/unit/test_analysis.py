"""Unit tests for bounded deterministic advisory Risk scenario analysis."""

from decimal import Decimal

from app.services.risk.contracts import (
    RiskErrorCode,
    ScenarioDefinition,
)
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.scenarios import run_risk_scenario_analysis

from tests.risk import _support as examples


def _scenario() -> ScenarioDefinition:
    """Build one exact combined relative and ratio shock."""
    return ScenarioDefinition(
        scenario_id="stress-1",
        shocks={"equity": Decimal("-0.10"), "drawdown": Decimal("0.05")},
        randomized=False,
        seed=None,
        assumptions=("equity down ten percent",),
    )


def test_analysis_is_immutable_and_deterministic() -> None:
    """Preserve input and return identical exact advisory projections."""
    config = examples._config()
    snapshot = examples._snapshot(config)
    before = snapshot.model_dump(warnings=False, mode="python")
    first = unwrap_risk_response(
        run_risk_scenario_analysis(snapshot, (_scenario(),), config, now=examples.NOW),
        operation="run_risk_scenario_analysis",
    )
    second = unwrap_risk_response(
        run_risk_scenario_analysis(snapshot, (_scenario(),), config, now=examples.NOW),
        operation="run_risk_scenario_analysis",
    )
    assert first == second
    assert first[0].projected["equity"] == Decimal(9000)
    assert first[0].projected["drawdown"] == Decimal("0.07")
    assert first[0].advisory_only is True
    assert snapshot.model_dump(warnings=False, mode="python") == before


def test_analysis_enforces_configured_payload_bound() -> None:
    """Reject scenario counts above the active configured bound."""
    config = examples._config().model_copy(update={"max_scenarios_per_run": 1})
    response = run_risk_scenario_analysis(
        examples._snapshot(config),
        (_scenario(), _scenario().model_copy(update={"scenario_id": "stress-2"})),
        config,
        now=examples.NOW,
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.PAYLOAD_TOO_LARGE.value
