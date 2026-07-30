"""WF-STR-PRI: generate vectorized decisions from genuine market evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import run_vectorized_strategy_signals
from tests.strategy.usage.workflows._support import (
    MarketProposalEvaluator,
    current_context,
    live_bars,
    print_market_frame,
    validated_config,
    validated_ref,
)

WORKFLOW_ID = "WF-STR-PRI"
STAGES = (
    "Accept genuine Data MarketDataset and optional IndicatorResult values.",
    "Fix the decision clock and immutable Strategy identity/configuration.",
    "Validate readiness, identity, ordering, and no-lookahead atomically.",
    "Run the approved hash-bound vectorized evaluator.",
    "Return deterministic create_trade_intent_value batch, replay evidence, and diagnostics.",
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
    print_market_frame(market)
    print("Input:", market.symbol, market.timeframe, market.record_count)

    # Stage 2: Freeze identity, config, and decision time.
    _stage(2)
    ref = validated_ref(timing_name="BAR_OPEN_PREVIOUS_CLOSE", supported_hooks=())
    config = validated_config()
    context = current_context("BAR_OPEN_PREVIOUS_CLOSE", market=market)
    print("Decision time:", context.decision_timestamp)

    # Stage 3: Public runner performs atomic boundary validation.
    _stage(3)
    print("Evaluator identity:", MarketProposalEvaluator.source_hash)

    # Stage 4: Run the approved evaluator.
    _stage(4)
    outcome = run_vectorized_strategy_signals(
        ref, config, market, (), context, MarketProposalEvaluator()
    )
    print("Evaluation:", outcome.status)
    if outcome.data is None:
        raise RuntimeError(f"Vectorized evaluation failed: {outcome.error}")

    # Stage 5 — OUTPUT BOUNDARY: Return atomic result or StandardResponse error.
    _stage(5)
    print(
        "Output:",
        type(outcome).__name__,
        tuple(
            {
                "intent_id": intent.intent_id,
                "symbol": intent.symbol,
                "side": intent.side,
                "quantity_hint": intent.quantity_hint,
                "lineage": dict(intent.lineage),
            }
            for intent in outcome.data.intents
        ),
    )


if __name__ == "__main__":
    main()
