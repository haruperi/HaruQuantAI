"""WF-RES-012: compare Research profiles across genuine market periods."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.serialization import canonical_digest
from app.services.research import (
    compare_research_profiles,
    create_research_value,
    get_research_value_field,
)
from tests.research.usage.workflows._support import prepared_dataset

WORKFLOW_ID = "WF-RES-012"
STAGES = (
    "Receive one prepared dataset backed by genuine MT5 market bars.",
    "Split observations into chronological non-overlapping comparison periods.",
    "Build compatible advisory profiles from calculated period evidence.",
    "Return period deltas, readiness stability, and explicit caveats.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def _scorecard(frame: object) -> object:
    """Build a scorecard from the observed positive-return share."""
    returns = frame["close"].pct_change().dropna()
    score = round(float((returns > 0).mean() * 100.0), 6)
    return create_research_value(
        "ResearchScorecard",
        "v1",
        ({"criterion": "positive_return_share", "score": score},),
        score,
        "REVIEW_READY",
        ("genuine_period_returns_measured",),
        (),
        True,
    )


def main() -> None:
    """Execute the documented cross-period comparison workflow."""
    print(f"{WORKFLOW_ID} — Compare Research Profiles Across Periods")
    print("INPUT BOUNDARY — genuine MT5 EURUSD bars prepared by Research")

    # Stage 1 — Receive one prepared dataset backed by genuine MT5 market bars.
    _stage(1)
    prepared = prepared_dataset()
    frame = get_research_value_field(prepared, "data")

    # Stage 2 — Split observations into chronological non-overlapping comparison periods.
    _stage(2)
    midpoint = len(frame) // 2
    periods = (frame.iloc[:midpoint].copy(), frame.iloc[midpoint:].copy())
    print("Observed periods:")
    print(
        frame[["open", "high", "low", "close"]]
        .iloc[[0, midpoint - 1, midpoint, -1]]
        .to_string()
    )

    # Stage 3 — Build compatible advisory profiles from calculated period evidence.
    _stage(3)
    configuration_hash = str(get_research_value_field(prepared, "configuration_hash"))
    snapshots = tuple(
        create_research_value(
            "ResearchProfileSnapshot",
            "v1",
            {"data": {"schema_version": "v1", "rows": len(period)}},
            _scorecard(period),
            canonical_digest(
                period[["open", "high", "low", "close"]]
                .reset_index()
                .to_dict(orient="records")
            ),
            configuration_hash,
            period.index[-1].to_pydatetime(),
            (),
            True,
        )
        for period in periods
    )

    # Stage 4 — Return period deltas, readiness stability, and explicit caveats.
    _stage(4)
    comparison = compare_research_profiles(snapshots)
    print("OUTPUT BOUNDARY — calculated period comparison:")
    for row in comparison["comparisons"]:
        print(row)
    print("Caveats:", comparison["caveats"])


if __name__ == "__main__":
    main()
