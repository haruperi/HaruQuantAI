"""WF-ANLT-007: run bounded seeded statistical validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import run_statistical_validation
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-007"
STAGES = (
    "Accept canonical finite numeric series and explicit bounded statistical config.",
    "Validate seed, iterations, confidence, alpha, and sample sufficiency.",
    "Run real bootstrap, permutation, multiple-comparison, and sample evidence.",
    "Repeat with the same seed to verify deterministic evidence.",
    "Return statistical SectionEvidence or explicit skipped/failure evidence.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies observed values and explicit bounds.
    _stage(1)
    _, config = examples._configured_result()
    values = tuple(float(index - 15) for index in range(30))
    print("Input observations:", len(values))
    # Stage 2: Show explicit deterministic configuration.
    _stage(2)
    print(
        "Seed/iterations:",
        config.statistics.seed,
        config.statistics.bootstrap_iterations,
    )
    # Stage 3: Run public statistical validation.
    _stage(3)
    first = examples.unwrap(run_statistical_validation(values, config=config))
    print("Metrics:", tuple(metric.metric_key for metric in first.metrics))
    # Stage 4: Verify seeded reproducibility.
    _stage(4)
    second = examples.unwrap(run_statistical_validation(values, config=config))
    print("Reproducible:", first == second)
    # Stage 5 — OUTPUT BOUNDARY: Return deterministic SectionEvidence.
    _stage(5)
    print("Output:", type(first).__name__, first.status)


if __name__ == "__main__":
    main()
