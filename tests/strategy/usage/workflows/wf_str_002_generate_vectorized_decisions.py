"""WF-STR-002: generate vectorized decisions from genuine market evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import StrategyTimingPolicy, run_vectorized_strategy_signals
from tests.strategy.unit.test_models import make_config, make_ref
from tests.strategy.usage.workflows._support import (
    CurrentNeutralEvaluator,
    current_context,
    live_bars,
)

WORKFLOW_ID = "WF-STR-002"
STAGES = (
    "Accept genuine Data MarketDataset and optional IndicatorResult values.",
    "Fix the decision clock and immutable Strategy identity/configuration.",
    "Validate readiness, identity, ordering, and no-lookahead atomically.",
    "Run the approved hash-bound vectorized evaluator.",
    "Return deterministic TradeIntent batch, replay evidence, and diagnostics.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Data supplies a genuine MT5-backed MarketDataset.
    _stage(1)
    market = live_bars()
    print("Input:", market.symbol, market.timeframe, market.record_count)

    # Stage 2: Freeze identity, config, and decision time.
    _stage(2)
    timing = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
    ref, config, context = (
        make_ref(timing=timing),
        make_config(),
        current_context(timing),
    )
    print("Decision time:", context.decision_timestamp)

    # Stage 3: Public runner performs atomic boundary validation.
    _stage(3)
    print("Evaluator identity:", CurrentNeutralEvaluator.source_hash)

    # Stage 4: Run the approved evaluator.
    _stage(4)
    outcome = run_vectorized_strategy_signals(
        ref, config, market, (), context, CurrentNeutralEvaluator()
    )
    print("Evaluation:", outcome.status)

    # Stage 5 — OUTPUT BOUNDARY: Return atomic result or StandardResponse error.
    _stage(5)
    print(
        "Output:",
        type(outcome).__name__,
        len(outcome.data.intents) if outcome.data else 0,
        "intents",
    )


if __name__ == "__main__":
    main()
