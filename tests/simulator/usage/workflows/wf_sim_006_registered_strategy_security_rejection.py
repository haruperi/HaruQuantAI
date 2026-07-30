"""WF-SIM-006: reject raw strategy code at the public boundary."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    dump_simulation_value,
    unwrap_simulation_response,
    validate_run_inputs,
)
from tests.simulator.usage.workflows._support import (
    backtest_request,
    live_market_dataset,
)

WORKFLOW_ID = "WF-SIM-006"
STAGES = (
    "Receive raw code, filesystem path, or an unapproved strategy reference.",
    "Validate reference-only run material at the public boundary.",
    "Return SIM_ARBITRARY_CODE_REJECTED before import, network, or engine creation.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented security-rejection workflow."""
    print(f"{WORKFLOW_ID} — Registered-Strategy Security Rejection")
    print("INPUT BOUNDARY — unapproved raw strategy source")

    # Stage 1 — Receive raw code, filesystem path, or an unapproved strategy reference.
    _stage(1)
    payload = dump_simulation_value(backtest_request(live_market_dataset())) | {
        "source_code": "import os"
    }

    # Stage 2 — Validate reference-only run material at the public boundary.
    _stage(2)
    try:
        unwrap_simulation_response(
            validate_run_inputs(payload),
            operation="simulation.workflow.wf_sim_006.validate_run_inputs",
        )
    except Exception as error:  # noqa: BLE001 - exception type is domain-private.
        rejected = error
    else:
        raise AssertionError("raw strategy code unexpectedly passed validation")

    # Stage 3 — Return SIM_ARBITRARY_CODE_REJECTED before import, network, or engine creation.
    _stage(3)
    assert rejected.code == "SIM_ARBITRARY_CODE_REJECTED"
    print(
        "OUTPUT BOUNDARY — controlled Simulation failure:",
        rejected.code,
    )


if __name__ == "__main__":
    main()
