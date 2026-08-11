"""WF-STR-010: evaluate recovered concrete signals atomically."""

from __future__ import annotations

import hashlib
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_symbol_metadata
from app.services.strategy import (
    create_strategy_evaluator,
    create_strategy_signal_evidence,
    evaluate_strategy_signals,
)
from tests.strategy.usage.workflows._support import (
    HASH,
    MODULE_PATH,
    STRATEGY_ID,
    STRATEGY_VERSION,
    current_context,
    live_bars,
    print_market_frame,
    validated_config,
    validated_ref,
)

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
    print_market_frame(market)
    metadata_response = get_symbol_metadata(source_id="mt5", symbol=market.symbol)
    point_size = (
        Decimal(str(metadata_response.data.point))
        if metadata_response.data is not None
        else Decimal("0.00001")
    )
    evidence = create_strategy_signal_evidence(
        evidence_id=hashlib.sha256(
            f"{market.request_id}:{market.available_at.isoformat()}".encode()
        ).hexdigest(),
        primary_market=market,
        related_markets={},
        point_size=point_size,
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    config = validated_config({"buy_magic_number": 17001, "sell_magic_number": 17002})
    print("Input:", market.symbol, market.record_count)

    # Stage 2: Construct the exact hash-bound approved evaluator.
    _stage(2)
    evaluator = create_strategy_evaluator(
        "random_walk",
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        module_path=MODULE_PATH,
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    print("Evaluator:", evaluator.module_path)

    # Stage 3: Public boundary performs atomic evidence checks.
    _stage(3)
    context = current_context("EVENT_DRIVEN", market=market)
    print("Decision time:", context.decision_timestamp)

    # Stage 4: Evaluate the concrete signals.
    _stage(4)
    outcome = evaluate_strategy_signals(
        validated_ref(), config, evidence, (), context, evaluator
    )
    print("Evaluation:", outcome.status)
    if outcome.data is None:
        raise RuntimeError(f"Signal evaluation failed: {outcome.error}")

    # Stage 5 — OUTPUT BOUNDARY: Return ordered signal tuple or structured failure.
    _stage(5)
    print(
        "Output signals:",
        tuple(signal.model_dump(mode="json") for signal in outcome.data),
    )


if __name__ == "__main__":
    main()
