"""WF-STR-SEC: build and hand off one canonical create_trade_intent_value."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import build_trade_intent
from tests.strategy.usage.workflows._support import (
    current_context,
    live_bars,
    print_market_frame,
    proposal_decision,
)

WORKFLOW_ID = "WF-STR-SEC"
STAGES = (
    "Accept approved Strategy decision metadata and fixed context.",
    "Canonicalize sizing, protection, identity, and lineage fields.",
    "Build stable intent and idempotency identifiers.",
    "Verify the result contains proposal evidence but no Risk or fill authority.",
    "Return create_trade_intent_value to the downstream Risk boundary.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Strategy supplies one validated proposal decision.
    _stage(1)
    market = live_bars(limit=12)
    print_market_frame(market)
    context = current_context("BAR_OPEN_PREVIOUS_CLOSE", market=market)
    decision = proposal_decision(context, market)
    print("Input decision:", decision.model_dump(mode="json"))

    # Stage 2: Public builder validates and canonicalizes proposal fields.
    _stage(2)
    outcome = build_trade_intent(decision, context, 0)
    print("Build status:", outcome.status)
    if outcome.data is None:
        raise RuntimeError(f"TradeIntent construction failed: {outcome.error}")

    # Stage 3: Stable identifiers are returned.
    _stage(3)
    intent = outcome.data
    print(
        "IDs:",
        intent.intent_id if intent else None,
        intent.idempotency_key if intent else None,
    )

    # Stage 4: Strategy has not granted downstream authority.
    _stage(4)
    payload = intent.model_dump(mode="json")
    print(
        "Authority fields absent:",
        not {"approved", "fill_id", "order_id"} & set(payload),
    )

    # Stage 5 — OUTPUT BOUNDARY: Hand off typed create_trade_intent_value or error.
    _stage(5)
    print("Output:", payload)


if __name__ == "__main__":
    main()
