"""WF-RES-007: label, validate, and calibrate market structure."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import MarketStructureConfig
from app.services.research.market_structure import (
    build_validation_summary,
    calibrate_market_structure,
    label_realized_market_behavior,
)
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-007"
STAGES = (
    "Receive persisted prediction context and later approved MT5-derived data.",
    "Label realized market behavior over the declared bar horizon.",
    "Build bounded validation and stability summaries.",
    "Calibrate candidates using the canonical scorer and return internal evidence.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented forward-validation workflow."""
    print(f"{WORKFLOW_ID} — Forward Validate and Calibrate Market Structure")
    print("INPUT BOUNDARY — persisted prediction plus later approved dataset")

    # Stage 1 — Receive persisted prediction context and later approved MT5-derived data.
    _stage(1)
    prepared = prepared_dataset()
    config = MarketStructureConfig(
        {"calibration_grid": [{"trend_threshold": 0.4}]},
        False,
        (2,),
        8,
        1,
    )

    # Stage 2 — Label realized market behavior over the declared bar horizon.
    _stage(2)
    realized = label_realized_market_behavior(
        prepared.data,
        symbol="EURUSD",
        timeframe="M1",
        config=config,
    )

    # Stage 3 — Build bounded validation and stability summaries.
    _stage(3)
    rows = [{"verdict": realized["verdict"], "symbol": "EURUSD", "confidence": 1.0}]
    summary = build_validation_summary(rows)

    # Stage 4 — Calibrate candidates using the canonical scorer and return internal evidence.
    _stage(4)
    calibration = calibrate_market_structure(
        run_rows=[
            {
                "efficiency_ratio": 0.6,
                "verdict": realized["verdict"],
                "symbol": "EURUSD",
            }
        ],
        validation_rows=[{"symbol": "EURUSD", "verdict": realized["verdict"]}],
        config=config,
        limits=limits(),
    )
    print("Validation rows:", summary["total_rows"])
    print(
        "OUTPUT BOUNDARY — internal validation/calibration evidence:",
        calibration["candidate_count"],
    )


if __name__ == "__main__":
    main()
