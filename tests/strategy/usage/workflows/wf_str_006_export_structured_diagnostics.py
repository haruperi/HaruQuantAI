"""WF-STR-006: export bounded and redacted Strategy diagnostics."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import export_strategy_diagnostics
from tests.strategy.usage.workflows._support import (
    current_context,
    live_bars,
    print_market_frame,
)

WORKFLOW_ID = "WF-STR-006"
STAGES = (
    "Accept fixed workflow context and bounded diagnostic facts.",
    "Recursively redact denied fields.",
    "Enforce registry-declared payload bounds.",
    "Build schema-valid diagnostics with trace and dependency status.",
    "Return safe diagnostics without persisting or routing an AuditEvent.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies safe facts at the Strategy boundary.
    _stage(1)
    market = live_bars(limit=12)
    print_market_frame(market)
    context = current_context("EVENT_DRIVEN", market=market)
    facts = {
        "strategy_id": "mean-reversion",
        "observed_close": str(market.records[-1].close),
        "password": "never-print-this",  # pragma: allowlist secret
    }
    print("Input keys:", tuple(facts))

    # Stage 2: Public exporter recursively redacts.
    _stage(2)
    outcome = export_strategy_diagnostics(context, facts)
    print("Export:", outcome.status)
    if outcome.data is None:
        raise RuntimeError(f"Diagnostics export failed: {outcome.error}")

    # Stage 3: Payload bound is enforced by the fixed context.
    _stage(3)
    print("Maximum bytes:", context.max_diagnostic_bytes)

    # Stage 4: Inspect canonical safe evidence.
    _stage(4)
    safe = outcome.data.safe_details
    print("Redacted password:", safe.get("password"))
    print("Safe diagnostics:", outcome.data.model_dump(mode="json"))

    # Stage 5 — OUTPUT BOUNDARY: Return typed diagnostics or StandardResponse error.
    _stage(5)
    print("Output:", type(outcome.data).__name__ if outcome.data else outcome.error)


if __name__ == "__main__":
    main()
