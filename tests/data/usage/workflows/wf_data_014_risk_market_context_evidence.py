"""WF-DATA-014: normalize Risk context from genuine MT5 evidence."""

from __future__ import annotations

import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    MarketContextEvidence,
    MarketContextRequest,
    get_market_context_evidence,
    get_spread_data,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-014"
STAGES = (
    "Retrieve current genuine MT5 spread evidence.",
    "Build a bounded Risk market-context request.",
    "Normalize provider facts with provenance and explicit missingness.",
    "Return evidence without producing a Risk verdict.",
)


class _MT5ContextProvider:
    """Expose already retrieved MT5 observations through the evidence protocol."""

    def __init__(self, spread: Decimal, as_of: object) -> None:
        self._spread = spread
        self._as_of = as_of

    def get_market_context(
        self, request: MarketContextRequest
    ) -> MarketContextEvidence:
        """Return normalized facts derived from genuine MT5 spread evidence."""
        return MarketContextEvidence(
            symbol=request.symbol,
            session_state=None,
            calendar_state=None,
            spread=self._spread,
            spread_unit="USD",
            liquidity=None,
            volatility=None,
            correlations={},
            crisis_flags=(),
            timezone=request.timezone,
            as_of=request.as_of,
            expires_at=request.as_of + timedelta(seconds=60),
            provenance={"source": "mt5", "observation": str(self._as_of)},
            missing_fields=("session", "calendar", "liquidity", "volatility"),
            request_id=request.request_id,
        )


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute genuine MT5 market-context normalization."""
    print(f"{WORKFLOW_ID} — Risk Market-Context Evidence")
    print("INPUT BOUNDARY — Risk requests declared EURUSD evidence")

    # Stage 1 — Retrieve current genuine MT5 spread evidence.
    _stage(1)
    spreads = get_spread_data(market_request("spreads", timeframe=None, limit=1))
    record = spreads.records[-1]
    spread = record.spread
    assert spread is not None

    # Stage 2 — Build a bounded Risk market-context request.
    _stage(2)
    request = MarketContextRequest(
        symbol="EURUSD",
        as_of=record.timestamp,
        max_age_seconds=60,
        requested_evidence=("spread",),
        timezone="UTC",
        request_id=generate_id("req"),
    )

    # Stage 3 — Normalize provider facts with provenance and explicit missingness.
    _stage(3)
    evidence = get_market_context_evidence(
        request,
        _MT5ContextProvider(spread, record.timestamp),
    )

    # Stage 4 — Return evidence without producing a Risk verdict.
    _stage(4)
    print("Context evidence:", evidence.spread, evidence.missing_fields)
    print("OUTPUT BOUNDARY — MarketContextEvidence v1, never a policy verdict")


if __name__ == "__main__":
    main()
