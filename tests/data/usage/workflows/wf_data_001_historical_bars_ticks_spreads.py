"""WF-DATA-001: retrieve historical MT5 bars, ticks, and spreads."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    ensure_source,
    evaluate_source_policy,
    get_market_data,
    get_spread_data,
    get_tick_data,
    inspect_dataset_quality,
    summarize_quality_remediation,
)
from tests.data.usage.workflows._support import market_request

WORKFLOW_ID = "WF-DATA-001"
STAGES = (
    "Validate request bounds, UTC range, workflow context, precision, stale policy, and fallback list.",
    "Compose MT5 and enforce readiness, capability, license, rate, timeout, and breaker policy.",
    "Resolve cache identity and apply the explicit stale-cache policy.",
    "Fetch bounded observations, normalize them, and inspect measured quality.",
    "Apply quality failure behavior and return typed datasets unchanged.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute the documented historical retrieval workflow."""
    print(f"{WORKFLOW_ID} — Historical Bars, Ticks, and Spreads")
    print("INPUT BOUNDARY — typed MarketDataRequest values")

    # Stage 1 — Validate request bounds, UTC range, workflow context, precision, stale policy, and fallback list.
    _stage(1)
    bars_request = market_request("bars", timeframe="M1")
    ticks_request = market_request("ticks", timeframe=None)
    spreads_request = market_request("spreads", timeframe=None)
    print("Validated request IDs:", bars_request.request_id, ticks_request.request_id)

    # Stage 2 — Compose MT5 and enforce readiness, capability, license, rate, timeout, and breaker policy.
    _stage(2)
    ensure_source("mt5", bars_request.request_id)
    plan = evaluate_source_policy(bars_request)
    print("Selected source plan:", plan.requested_source)

    # Stage 3 — Resolve cache identity and apply the explicit stale-cache policy.
    _stage(3)
    assert bars_request.use_cache is False
    assert bars_request.stale_cache_policy == "refresh"
    print("Cache policy:", bars_request.use_cache, bars_request.stale_cache_policy)

    # Stage 4 — Fetch bounded observations, normalize them, and inspect measured quality.
    _stage(4)
    bars = get_market_data(bars_request)
    ticks = get_tick_data(ticks_request)
    spreads = get_spread_data(spreads_request)
    reports = tuple(
        inspect_dataset_quality(dataset) for dataset in (bars, ticks, spreads)
    )
    print("Record counts:", bars.record_count, ticks.record_count, spreads.record_count)

    # Stage 5 — Apply quality failure behavior and return typed datasets unchanged.
    _stage(5)
    remediation = tuple(summarize_quality_remediation(report) for report in reports)
    print("Quality states:", tuple(report.quality_status for report in reports))
    print("Remediation summaries:", remediation)
    print("OUTPUT BOUNDARY — three typed MarketDataset values")


if __name__ == "__main__":
    main()
