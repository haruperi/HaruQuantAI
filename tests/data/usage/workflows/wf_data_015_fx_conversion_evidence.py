"""WF-DATA-015: derive exact FX evidence from a genuine MT5 EURUSD bar."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    FXConversionRequest,
    FXRateLeg,
    get_fx_conversion_evidence,
    get_market_data,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-015"
STAGES = (
    "Retrieve one genuine MT5 EURUSD observation.",
    "Validate currencies, UTC as-of, age, and allowed path policy.",
    "Publish the exact direct MT5 rate leg and provenance.",
    "Return deterministic FXConversionEvidence without a fabricated rate.",
)


class _MT5RateProvider:
    """Expose one already retrieved genuine direct FX rate."""

    def __init__(self, rate: Decimal, observed_at: datetime) -> None:
        self._rate = rate
        self._observed_at = observed_at

    def get_rate_leg(
        self,
        *,
        source_currency: str,
        target_currency: str,
        as_of: datetime,
        request_id: str,
    ) -> FXRateLeg:
        """Return the exact direct MT5 leg."""
        del request_id
        return FXRateLeg(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=self._rate,
            source_id="mt5",
            provider_symbol="EURUSD",
            as_of=min(self._observed_at, as_of),
            provenance={"source": "genuine-mt5-bar"},
        )


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute genuine direct FX conversion evidence."""
    print(f"{WORKFLOW_ID} — FX Conversion Evidence")
    print("INPUT BOUNDARY — EUR to USD conversion request")

    # Stage 1 — Retrieve one genuine MT5 EURUSD observation.
    _stage(1)
    bars = get_market_data(market_request("bars", timeframe="M1", limit=1))
    bar = bars.records[-1]

    # Stage 2 — Validate currencies, UTC as-of, age, and allowed path policy.
    _stage(2)
    request = FXConversionRequest(
        source_currency="EUR",
        target_currency="USD",
        as_of=bar.timestamp + timedelta(seconds=1),
        max_age_seconds=120,
        allowed_intermediates=("GBP",),
        max_legs=2,
        path_policy_id="direct-first",
        path_policy_version="v1",
        request_id=generate_id("req"),
    )

    # Stage 3 — Publish the exact direct MT5 rate leg and provenance.
    _stage(3)
    evidence = get_fx_conversion_evidence(
        request,
        _MT5RateProvider(bar.close, bar.timestamp),
    )

    # Stage 4 — Return deterministic FXConversionEvidence without a fabricated rate.
    _stage(4)
    assert evidence.composite_rate == bar.close
    print("Direct composite rate:", evidence.composite_rate)
    print("OUTPUT BOUNDARY — exact FXConversionEvidence v1")


if __name__ == "__main__":
    main()
