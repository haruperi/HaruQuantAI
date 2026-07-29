"""WF-DATA-015: derive exact FX evidence from a genuine MT5 EURUSD bar."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_fx_conversion_request,
    build_fx_rate_leg,
    data_start_time,
    get_fx_conversion_evidence,
    get_market_data,
    run_data_operation,
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

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
    ) -> object:
        """Return the exact direct MT5 leg."""

        def _build() -> object:
            return build_fx_rate_leg(
                source_currency=source_currency,
                target_currency=target_currency,
                rate=self._rate,
                source_id="mt5",
                provider_symbol="EURUSD",
                as_of=min(self._observed_at, as_of),
                provenance={"source": "genuine-mt5-bar"},
            )

        return run_data_operation(
            operation="data.evidence.fx_rate_provider.get_rate_leg",
            request_id=request_id,
            start_time=data_start_time(),
            raw=_build,
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

    with (
        tempfile.TemporaryDirectory(prefix="wf-data-015-") as directory,
        isolated_runtime(Path(directory)),
    ):
        request_id = generate_id("req")

        # Stage 1 — Retrieve one genuine MT5 EURUSD observation.
        _stage(1)
        bars_resp = get_market_data(market_request("bars", timeframe="M1", limit=1))
        bars = unwrap_data_response(
            bars_resp, operation="get_market_data", request_id=request_id
        )
        bar = bars.records[-1]

        # Stage 2 — Validate currencies, UTC as-of, age, and allowed path policy.
        _stage(2)
        request = build_fx_conversion_request(
            source_currency="EUR",
            target_currency="USD",
            as_of=bar.timestamp + timedelta(seconds=1),
            max_age_seconds=120,
            allowed_intermediates=("GBP",),
            max_legs=2,
            path_policy_id="direct-first",
            path_policy_version="v1",
            request_id=request_id,
        )

        # Stage 3 — Publish the exact direct MT5 rate leg and provenance.
        _stage(3)
        evidence_resp = get_fx_conversion_evidence(
            request,
            _MT5RateProvider(bar.close, bar.timestamp),
        )
        evidence = unwrap_data_response(
            evidence_resp, operation="get_fx_conversion_evidence", request_id=request_id
        )

        # Stage 4 — Return deterministic FXConversionEvidence without a fabricated rate.
        _stage(4)
        assert evidence.composite_rate == bar.close
        print("Direct composite rate:", evidence.composite_rate)
    print("OUTPUT BOUNDARY — exact FXConversionEvidence v1")


if __name__ == "__main__":
    main()
