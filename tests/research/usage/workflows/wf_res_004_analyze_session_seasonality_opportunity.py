"""WF-RES-004: tag sessions and compute advisory seasonality."""

from __future__ import annotations

import sys
from datetime import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import SessionConfig
from app.services.research.seasonality import (
    SeasonalityFilters,
    run_seasonality,
    tag_sessions,
)
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-004"
STAGES = (
    "Receive prepared genuine MT5 OHLCVS and an approved UTC session policy.",
    "Tag copied observations using canonical overlap precedence.",
    "Run bounded seasonality summaries with explicit sparse-bucket warnings.",
    "Return advisory opportunity summaries without trading authority.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented session-seasonality workflow."""
    print(f"{WORKFLOW_ID} — Analyze Session and Seasonality Opportunity")
    print("INPUT BOUNDARY — PreparedDataset and SessionConfig")

    # Stage 1 — Receive prepared genuine MT5 OHLCVS and an approved UTC session policy.
    _stage(1)
    prepared = prepared_dataset()
    sessions = SessionConfig(
        "UTC",
        {
            "sydney": (time(21), time(6)),
            "tokyo": (time(0), time(9)),
            "london": (time(7), time(16)),
            "new_york": (time(12), time(21)),
        },
        ("london", "new_york", "tokyo", "sydney"),
    )

    # Stage 2 — Tag copied observations using canonical overlap precedence.
    _stage(2)
    tagged, warnings = tag_sessions(prepared.data, config=sessions)

    # Stage 3 — Run bounded seasonality summaries with explicit sparse-bucket warnings.
    _stage(3)
    summary = run_seasonality(
        prepared,
        sessions=sessions,
        filters=SeasonalityFilters(),
        limits=limits(),
    )

    # Stage 4 — Return advisory opportunity summaries without trading authority.
    _stage(4)
    print("Tagged rows/warnings:", len(tagged), len(warnings))
    print("OUTPUT BOUNDARY — advisory seasonality summary rows:", summary["row_count"])


if __name__ == "__main__":
    main()
