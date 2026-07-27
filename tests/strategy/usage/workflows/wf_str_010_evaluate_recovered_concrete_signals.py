"""WF-STR-010: evaluate recovered concrete signals atomically."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import RandomWalkEvaluator, evaluate_strategy_signals
from tests.strategy.unit.test_models import (
    HASH,
    make_ref,
    make_signal_config,
    make_signal_evidence,
)
from tests.strategy.usage.workflows._support import current_context, live_bars

WORKFLOW_ID = "WF-STR-010"
STAGES = (
    "Accept exact registry reference, config, point-in-time Data, and optional Indicators evidence.",
    "Verify evaluator identity and immutable hashes.",
    "Validate availability, alignment, and output identity atomically.",
    "Run the approved concrete evaluator without legacy code loading.",
    "Return an ordered immutable signal tuple or structured failure.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies genuine point-in-time Data evidence.
    _stage(1)
    market = live_bars()
    evidence = make_signal_evidence(market)
    config = make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20})
    print("Input:", market.symbol, market.record_count)

    # Stage 2: Construct the exact hash-bound approved evaluator.
    _stage(2)
    evaluator = RandomWalkEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    print("Evaluator:", evaluator.module_path)

    # Stage 3: Public boundary performs atomic evidence checks.
    _stage(3)
    context = current_context()
    print("Decision time:", context.decision_timestamp)

    # Stage 4: Evaluate the concrete signals.
    _stage(4)
    outcome = evaluate_strategy_signals(
        make_ref(), config, evidence, (), context, evaluator
    )
    print("Evaluation:", outcome.status)

    # Stage 5 — OUTPUT BOUNDARY: Return ordered signal tuple or structured failure.
    _stage(5)
    print("Output signals:", tuple(signal.signal_name for signal in outcome.data or ()))


if __name__ == "__main__":
    main()
