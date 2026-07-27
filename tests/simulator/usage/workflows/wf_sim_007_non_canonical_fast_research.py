"""WF-SIM-007: run an explicitly non-canonical approximation."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import run_fast_research
from tests.simulator.usage.workflows._support import (
    authority,
    backtest_request,
    dependencies,
    live_tick_dataset,
)

WORKFLOW_ID = "WF-SIM-007"
STAGES = (
    "Receive authenticated request explicitly selecting fast_research.",
    "Validate non-canonical scope and prohibited official claims.",
    "Run the bounded approximation through run_fast_research().",
    "Return disclosed FastResearchResult with canonical=false.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented fast-research workflow."""
    print(f"{WORKFLOW_ID} — Non-Canonical Fast Research")
    print("INPUT BOUNDARY — explicit fast_research request and MT5 evidence")

    # Stage 1 — Receive authenticated request explicitly selecting fast_research.
    _stage(1)
    dataset = live_tick_dataset()
    request = backtest_request(
        dataset,
        runtime_profile="fast_research",
        canonical=False,
    )

    # Stage 2 — Validate non-canonical scope and prohibited official claims.
    _stage(2)
    assert request.runtime_profile == "fast_research"
    assert not request.canonical

    # Stage 3 — Run the bounded approximation through run_fast_research().
    _stage(3)
    with tempfile.TemporaryDirectory(prefix="wf-sim-007-") as directory:
        result = run_fast_research(
            request,
            authority(request),
            dependencies(Path(directory), dataset),
        )

    # Stage 4 — Return disclosed FastResearchResult with canonical=false.
    _stage(4)
    print(
        "OUTPUT BOUNDARY — typed FastResearchResult:",
        result.canonical,
        result.assumptions,
    )


if __name__ == "__main__":
    main()
