"""WF-SIM-012: validate observed FX evidence, margin, and execution costs."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    calculate_execution_costs,
    calculate_margin,
    create_simulation_value,
    dump_simulation_value,
    unwrap_simulation_response,
    validate_fx_evidence,
)
from tests.simulator.usage.workflows._support import (
    fx_evidence,
    live_tick_dataset,
)

WORKFLOW_ID = "WF-SIM-012"
STAGES = (
    "Retrieve genuine MT5 ticks and build Data-owned FX evidence.",
    "Validate FX freshness and compatibility at the Simulator boundary.",
    "Calculate explicit execution costs and observed-price margin.",
    "Display the source tick, validated FX lineage, costs, and margin.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Calculate exact costs using a genuine MT5-derived FX observation."""
    print("INPUT BOUNDARY — genuine MT5 tick and explicit cost contracts")
    # Stage 1 — Retrieve genuine MT5 ticks and build Data-owned FX evidence.
    _stage(1)
    dataset = live_tick_dataset()
    evidence = fx_evidence(dataset)
    # Stage 2 — Validate FX freshness and compatibility at the Simulator boundary.
    _stage(2)
    validated = unwrap_simulation_response(
        validate_fx_evidence(evidence, as_of=dataset.end),
        operation="simulation.workflow.wf_sim_012.validate_fx_evidence",
    )
    # Stage 3 — Calculate explicit execution costs and observed-price margin.
    _stage(3)
    cost_input = create_simulation_value(
        "ExecutionCostInput",
        volume=Decimal(1),
        side="BUY",
        rollover_multiplier=Decimal(0),
    )
    cost_model = create_simulation_value(
        "ExecutionCostModel",
        commission_per_lot_per_side=Decimal("3.5"),
        long_swap_per_lot_rollover=Decimal("1.25"),
        short_swap_per_lot_rollover=Decimal("0.75"),
    )
    costs = unwrap_simulation_response(
        calculate_execution_costs(cost_input, cost_model),
        operation="simulation.workflow.wf_sim_012.calculate_execution_costs",
    )
    observed_price = dataset.records[-1].ask
    margin = unwrap_simulation_response(
        calculate_margin(
            Decimal(1),
            observed_price,
            Decimal(100_000),
            Decimal(100),
        ),
        operation="simulation.workflow.wf_sim_012.calculate_margin",
    )
    # Stage 4 — Display the source tick, validated FX lineage, costs, and margin.
    _stage(4)
    print(f"{WORKFLOW_ID} — FX Margin and Execution Costs")
    print("Observed MT5 tick:", dataset.records[-1].model_dump(mode="python"))
    print("Validated FX evidence:", dump_simulation_value(validated))
    print("Exact cost breakdown:", dict(costs))
    print(
        "Exact margin evidence:",
        {
            "observed_ask": observed_price,
            "contract_size": Decimal(100_000),
            "leverage": Decimal(100),
            "required_margin": margin,
        },
    )
    print("OUTPUT BOUNDARY — validated FX, execution costs, and required margin")


if __name__ == "__main__":
    main()
