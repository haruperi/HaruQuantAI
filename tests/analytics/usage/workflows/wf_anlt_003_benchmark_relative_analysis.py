"""WF-ANLT-003: calculate benchmark-relative Analytics evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import align_benchmark_series, calculate_benchmark_evidence
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-003"
STAGES = (
    "Accept canonical strategy result and Data-owned benchmark bars.",
    "Normalize UTC timestamps, window bounds, duplicates, and intersection.",
    "Align strategy and benchmark observations deterministically.",
    "Calculate only approved currency-valid benchmark metrics.",
    "Return benchmark SectionEvidence or explicit skipped/undefined evidence.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Canonical result contains Data-owned benchmark evidence.
    _stage(1)
    result, config = examples._configured_result(benchmark=True)
    points = tuple(result.benchmark["points"]) if result.benchmark else ()
    print("Input benchmark points:", len(points))
    # Stage 2: Build explicit UTC strategy observation points.
    _stage(2)
    strategy = tuple(
        {"timestamp": point["timestamp"], "value": float(index)}
        for index, point in enumerate(points)
    )
    print("UTC strategy points:", len(strategy))
    # Stage 3: Align through the public deterministic operation.
    _stage(3)
    aligned_strategy, aligned_benchmark = align_benchmark_series(strategy, points)
    print("Aligned:", len(aligned_strategy), len(aligned_benchmark))
    # Stage 4: Calculate approved benchmark evidence.
    _stage(4)
    section = calculate_benchmark_evidence(result, config=config)
    print("Metrics:", tuple(metric.metric_key for metric in section.metrics))
    # Stage 5 — OUTPUT BOUNDARY: Return benchmark SectionEvidence.
    _stage(5)
    print("Output:", type(section).__name__, section.status)


if __name__ == "__main__":
    main()
