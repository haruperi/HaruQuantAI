"""WF-STR-009: reject an evaluator not bound to immutable registry hashes."""

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

WORKFLOW_ID = "WF-STR-009"
STAGES = (
    "Accept only a registry-bound evaluator and typed execution evidence.",
    "Compare immutable evaluator identity and hashes before execution.",
    "Reject the mismatched evaluator without importing arbitrary code.",
    "Expose only a redacted deterministic Strategy error.",
    "Return no intents and perform no downstream mutation.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented fail-closed workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller attempts to supply a hash-mismatched evaluator.
    _stage(1)
    evaluator = MarketProposalEvaluator()
    evaluator.source_hash = "f" * 64
    market = live_bars()
    print_market_frame(market)
    print("Input evaluator hash prefix:", evaluator.source_hash[:8])

    # Stage 2: Public runner verifies immutable identity first.
    _stage(2)
    outcome = run_vectorized_strategy_signals(
        validated_ref(
            timing_name="BAR_OPEN_PREVIOUS_CLOSE",
            supported_hooks=(),
        ),
        validated_config(),
        market,
        (),
        current_context("BAR_OPEN_PREVIOUS_CLOSE", market=market),
        evaluator,
    )
    print("Identity check:", outcome.status)

    # Stage 3: No arbitrary evaluator body is executed.
    _stage(3)
    print("Evaluator rejected:", outcome.status == "error")

    # Stage 4: Error remains structured and redacted.
    _stage(4)
    print("Error code:", outcome.error.code if outcome.error else None)
    if outcome.error is None or (
        outcome.error.code != "STRATEGY_ARTIFACT_HASH_MISMATCH"
    ):
        raise RuntimeError("Hash-mismatched evaluator did not fail closed")

    # Stage 5 — OUTPUT BOUNDARY: Return error with no partial intents or mutation.
    _stage(5)
    print("Output data:", outcome.data)


if __name__ == "__main__":
    main()
