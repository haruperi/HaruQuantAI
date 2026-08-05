"""WF-SIM-004: block severe Data quality before execution."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import run_backtest, unwrap_simulation_response
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_tick_dataset,
)

WORKFLOW_ID = "WF-SIM-004"
STAGES = (
    "Receive Data-owned manifest and normalized genuine MT5 dataset.",
    "Mark the measured severe quality failure on the typed Data evidence.",
    "Run canonical validation before engine creation.",
    "Return structured failure with no execution state or published result.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented fail-closed quality workflow."""
    print(f"{WORKFLOW_ID} — Severe Data-Quality Block")
    print("INPUT BOUNDARY — Data-owned genuine MT5 dataset and quality manifest")

    # Stage 1 — Receive Data-owned manifest and normalized genuine MT5 dataset.
    _stage(1)
    original = live_tick_dataset()

    # Stage 2 — Mark the measured severe quality failure on the typed Data evidence.
    _stage(2)
    failed = original.model_copy(
        update={
            "quality_report": original.quality_report.model_copy(
                update={
                    "quality_status": "critical",
                    "quality_decision": "rejected",
                    "quality_score": 0,
                }
            )
        }
    )
    request = backtest_request(failed)

    # Stage 3 — Run canonical validation before engine creation.
    _stage(3)
    with tempfile.TemporaryDirectory(prefix="wf-sim-004-") as directory:
        deps = dependencies(Path(directory), failed)
        try:
            response = run_backtest(request, authority(request), deps)
            unwrap_simulation_response(
                response,
                operation="simulation.workflow.wf_sim_004.run_backtest",
            )
        except Exception as error:  # noqa: BLE001 - exception type is private.
            blocked = error
        else:
            raise AssertionError("failed-quality data unexpectedly executed")

        # Stage 4 — Return structured failure with no execution state or published result.
        _stage(4)
        assert not tuple(deps.artifact_root.rglob("manifest.json"))
        print(
            "OUTPUT BOUNDARY — controlled Simulation failure:",
            blocked.code,
        )


if __name__ == "__main__":
    main()
