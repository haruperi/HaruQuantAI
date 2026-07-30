"""WF-RISK-010: run deterministic advisory scenario analysis."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import create_scenario_definition, run_risk_scenario_analysis
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-010"
STAGES = (
    "Accept immutable snapshot and bounded create_scenario_definition values.",
    "Validate declared shocks, assumptions, randomization, and seed.",
    "Calculate deterministic baseline/projected differences.",
    "Preserve source snapshot and mark results advisory-only and unapproved.",
    "Return registered ScenarioResult v1 values.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies immutable snapshot and declared scenario.
    _stage(1)
    config = examples._config()
    snapshot = examples._snapshot(config)
    scenario = create_scenario_definition(
        scenario_id="combined-stress",
        shocks={"equity": Decimal("-0.15"), "portfolio_correlation": Decimal("0.30")},
        randomized=False,
        seed=None,
        assumptions=("declared aggregate stress",),
    )
    before = snapshot.model_dump(warnings=False, mode="python")
    print("Input scenario:", scenario.scenario_id)
    # Stage 2: Validate explicit bounded shock definition.
    _stage(2)
    print("Shocks:", dict(scenario.shocks))
    # Stage 3: Run the public deterministic analyzer.
    _stage(3)
    results = unwrap_risk_response(
        run_risk_scenario_analysis(snapshot, (scenario,), config, now=examples.NOW),
        operation="run_risk_scenario_analysis",
    )
    print("Results:", len(results))
    # Stage 4: Verify advisory/no-mutation boundary.
    _stage(4)
    print(
        "Advisory:",
        results[0].advisory_only,
        "approved:",
        results[0].approved,
        "unchanged:",
        before == snapshot.model_dump(warnings=False, mode="python"),
    )
    # Stage 5 — OUTPUT BOUNDARY: Return ScenarioResult v1 tuple.
    _stage(5)
    print("Output:", type(results[0]).__name__)


if __name__ == "__main__":
    main()
