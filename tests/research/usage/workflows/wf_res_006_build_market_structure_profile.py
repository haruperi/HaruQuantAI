"""WF-RES-006: build market-structure profile, quality, and fit."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import (
    build_market_structure_profile,
    build_strategy_fit,
    create_research_value,
    evaluate_market_structure_quality,
)
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-006"
STAGES = (
    "Receive prepared genuine MT5 data and bounded market-structure policy.",
    "Build the canonical market-structure profile.",
    "Optionally evaluate bounded temporal and parameter quality.",
    "Build and return advisory strategy-fit evidence.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def _config() -> object:
    """Return bounded market-structure configuration."""
    return create_research_value(
        "MarketStructureConfig",
        {
            "swing_window": 3,
            "atr_period": 5,
            "trend_threshold": 0.5,
            "range_threshold": 0.2,
            "calibration_grid": [{"trend_threshold": 0.4}],
        },
        True,
        (10, 20),
        128,
        5,
    )


def main() -> None:
    """Execute the documented market-structure workflow."""
    print(f"{WORKFLOW_ID} — Build Market-Structure Profile")
    print("INPUT BOUNDARY — PreparedDataset plus MarketStructureConfig")

    # Stage 1 — Receive prepared genuine MT5 data and bounded market-structure policy.
    _stage(1)
    prepared = prepared_dataset()
    config = _config()

    # Stage 2 — Build the canonical market-structure profile.
    _stage(2)
    profile = build_market_structure_profile(prepared, config=config, limits=limits())

    # Stage 3 — Optionally evaluate bounded temporal and parameter quality.
    _stage(3)
    quality = evaluate_market_structure_quality(
        prepared, config=config, limits=limits()
    )

    # Stage 4 — Build and return advisory strategy-fit evidence.
    _stage(4)
    fit = build_strategy_fit(profile)
    print("Quality windows:", len(quality.stability.get("windows", [])))
    print(
        "OUTPUT BOUNDARY — MarketStructureProfile and advisory fit:",
        profile.verdict,
        fit["primary_archetype"],
    )


if __name__ == "__main__":
    main()
