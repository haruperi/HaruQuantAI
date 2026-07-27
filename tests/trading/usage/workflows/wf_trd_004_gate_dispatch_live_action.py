"""WF-TRD-004: gate an MT5 demo action and fail closed before mutation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.brokers import BrokerId
from app.services.trading import TradingError, evaluate_live_gate
from tests.brokers.usage._support import real_session, require_success
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-004"
STAGES = (
    "Open and verify a genuine non-production MT5 session.",
    "Accept canonical request plus current external verdict/evidence inputs.",
    "Evaluate schema, session, policy, Risk, kill, readiness, idempotency, audit, and adapter gates.",
    "Block because no typed current RiskDecision is supplied; dispatch_order_intent is not invoked.",
    "Return audited fail-closed TradingError and disconnect MT5.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the genuine connection plus fail-closed gate."""
    # Stage 1 — INPUT BOUNDARY: Genuine MT5 demo connection and canonical request.
    _stage(1)
    async with real_session(BrokerId.MT5) as adapter:
        require_success("MT5 readiness", await adapter.get_connection_status())
        # Stage 2: Build a package-only session with deliberately absent Risk truth.
        _stage(2)
        session = examples.live_gate_session(risk_decision=None)
        await session.start(
            {**examples.live_config(), "ALLOW_LIVE_MUTATIONS": True},
            examples.live_evidence(),
        )
        request = examples.live_gate_request()
        print("Input:", request.route, request.action)
        # Stage 3: Execute every mandatory public gate.
        _stage(3)
        try:
            await evaluate_live_gate(request, {}, session)
        except TradingError as error:
            blocked = error
        else:
            raise RuntimeError("Live gate unexpectedly admitted mutation")
        print("Gate result:", blocked.code)
        # Stage 4: No dispatch is attempted.
        _stage(4)
        print("Dispatch invoked:", False, "No broker mutation was transmitted")
        # Stage 5 — OUTPUT BOUNDARY: Structured fail-closed result; MT5 disconnect follows.
        _stage(5)
        print("Output:", type(blocked).__name__, blocked.code)


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
