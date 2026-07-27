"""WF-ANLT-013: build non-binding portfolio allocation evidence."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import (
    build_portfolio_allocation_evidence,
    build_portfolio_performance_report,
)
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-013"
STAGES = (
    "Accept component reports and exact PortfolioSimulationResult plus FX evidence.",
    "Validate source schemas, component pairing, window, base currency, FX, and finite values.",
    "Build the currency-safe internal portfolio performance report.",
    "Project performance, dependence, concentration, caveats, and FX lineage.",
    "Return non-binding PortfolioAllocationEvidence v1.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Simulation/Portfolio supplies exact immutable evidence.
    _stage(1)
    first, config = examples._report(source_id="simulation-result-1")
    second, _ = examples._report(profit=Decimal(20), source_id="simulation-result-2")
    simulation = examples._portfolio_simulation_result()
    print("Input components:", len(simulation["component_results"]))
    # Stage 2: Validate exact receiver-owned inputs.
    _stage(2)
    print(
        "Measurement window:",
        simulation["measurement_start"],
        simulation["measurement_end"],
    )
    # Stage 3: Demonstrate internal currency-safe aggregation.
    _stage(3)
    portfolio = build_portfolio_performance_report(
        (first, second), base_currency="USD", fx_evidence=None, config=config
    )
    print("Internal portfolio sections:", len(portfolio.sections))
    # Stage 4: Project complete allocation evidence.
    _stage(4)
    evidence = build_portfolio_allocation_evidence(
        (first, second),
        base_currency="USD",
        fx_evidence=None,
        config=config,
        portfolio_simulation_result=simulation,
    )
    print(
        "Dependence/concentration:",
        evidence.dependence_evidence.status,
        evidence.concentration_evidence.status,
    )
    # Stage 5 — OUTPUT BOUNDARY: Return non-binding cross-domain evidence.
    _stage(5)
    print("Output:", type(evidence).__name__, evidence.non_binding)


if __name__ == "__main__":
    main()
