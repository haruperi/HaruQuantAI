"""WF-STR-SEC: build and hand off one canonical TradeIntent."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import build_trade_intent
from tests.strategy.unit.test_models import make_context, make_decision

WORKFLOW_ID = "WF-STR-SEC"
STAGES = (
    "Accept approved Strategy decision metadata and fixed context.",
    "Canonicalize sizing, protection, identity, and lineage fields.",
    "Build stable intent and idempotency identifiers.",
    "Verify the result contains proposal evidence but no Risk or fill authority.",
    "Return TradeIntent to the downstream Risk boundary.",
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
    decision, context = make_decision(), make_context()
    print("Input:", decision.action, decision.symbol, decision.side)

    # Stage 2: Public builder validates and canonicalizes proposal fields.
    _stage(2)
    outcome = build_trade_intent(decision, context, 0)
    print("Build status:", outcome.status)

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
    payload = intent.model_dump(mode="json") if intent else {}
    print(
        "Authority fields absent:",
        not {"approved", "fill_id", "order_id"} & set(payload),
    )

    # Stage 5 — OUTPUT BOUNDARY: Hand off typed TradeIntent or error.
    _stage(5)
    print("Output:", type(intent).__name__ if intent else outcome.error)


if __name__ == "__main__":
    main()
