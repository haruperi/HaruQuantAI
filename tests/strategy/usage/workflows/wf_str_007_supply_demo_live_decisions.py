"""WF-STR-007: supply proposals to a demo/live runtime boundary."""

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

WORKFLOW_ID = "WF-STR-007"
STAGES = (
    "Trading supplies genuine prepared Data evidence and fixed runtime context.",
    "Strategy validates and runs the approved evaluator.",
    "A neutral decision ends the cycle; a proposal becomes create_trade_intent_value only.",
    "Risk remains the independent authority for every proposal.",
    "Return no action or proposal evidence without execution/fill fields.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Runtime supplies genuine MT5-backed Data evidence.
    _stage(1)
    market = live_bars()
    print_market_frame(market)
    context = current_context("BAR_OPEN_PREVIOUS_CLOSE", market=market)
    print("Input:", market.symbol, market.available_at)

    # Stage 2: Evaluate through Strategy's public boundary.
    _stage(2)
    outcome = run_vectorized_strategy_signals(
        validated_ref(
            timing_name="BAR_OPEN_PREVIOUS_CLOSE",
            supported_hooks=(),
        ),
        validated_config(),
        market,
        (),
        context,
        MarketProposalEvaluator(),
    )
    print("Evaluation:", outcome.status)
    if outcome.data is None:
        raise RuntimeError(f"Strategy evaluation failed: {outcome.error}")

    # Stage 3: Neutral evaluator emits no intent.
    _stage(3)
    intents = outcome.data.intents
    print(
        "Proposals:",
        tuple(intent.model_dump(mode="json") for intent in intents),
    )

    # Stage 4: Confirm no Risk authority was synthesized.
    _stage(4)
    print(
        "Risk approval synthesized:",
        any(hasattr(intent, "risk_approved") for intent in intents),
    )

    # Stage 5 — OUTPUT BOUNDARY: Return proposal-only Strategy result.
    _stage(5)
    print("Output:", type(outcome).__name__, outcome.status)


if __name__ == "__main__":
    main()
