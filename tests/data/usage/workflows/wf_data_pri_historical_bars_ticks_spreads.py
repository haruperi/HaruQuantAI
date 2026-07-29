"""WF-DATA-PRI: retrieve historical MT5 bars, ticks, and spreads."""

from __future__ import annotations

import sys
import tempfile
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
    unwrap_data_response,
)
from app.utils import generate_id
from tests.data.usage.workflows._support import isolated_runtime, market_request

WORKFLOW_ID = "WF-DATA-PRI"
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

    with (
        tempfile.TemporaryDirectory(prefix="wf-data-pri-") as directory,
        isolated_runtime(Path(directory)),
    ):
        request_id = generate_id("req")

        # Stage 1 — Validate request bounds, UTC range, workflow context, precision, stale policy, and fallback list.
        _stage(1)
        bars_request = market_request("bars", timeframe="M1")
        ticks_request = market_request("ticks", timeframe=None)
        spreads_request = market_request("spreads", timeframe=None)
        print(
            "Validated request IDs:", bars_request.request_id, ticks_request.request_id
        )

        # Stage 2 — Compose MT5 and enforce readiness, capability, license, rate, timeout, and breaker policy.
        _stage(2)
        ensure_resp = ensure_source("mt5", bars_request.request_id)
        unwrap_data_response(
            ensure_resp, operation="ensure_source", request_id=request_id
        )
        plan_resp = evaluate_source_policy(bars_request)
        plan = unwrap_data_response(
            plan_resp, operation="evaluate_source_policy", request_id=request_id
        )
        print("Selected source plan:", plan.requested_source)

        # Stage 3 — Resolve cache identity and apply the explicit stale-cache policy.
        _stage(3)
        assert bars_request.use_cache is False
        assert bars_request.stale_cache_policy == "refresh"
        print("Cache policy:", bars_request.use_cache, bars_request.stale_cache_policy)

        # Stage 4 — Fetch bounded observations, normalize them, and inspect measured quality.
        _stage(4)
        bars = unwrap_data_response(
            get_market_data(bars_request),
            operation="get_market_data",
            request_id=request_id,
        )
        ticks = unwrap_data_response(
            get_tick_data(ticks_request),
            operation="get_tick_data",
            request_id=request_id,
        )
        spreads = unwrap_data_response(
            get_spread_data(spreads_request),
            operation="get_spread_data",
            request_id=request_id,
        )
        reports = tuple(
            unwrap_data_response(
                inspect_dataset_quality(dataset),
                operation="data.quality.inspect_dataset_quality",
                request_id=request_id,
            )
            for dataset in (bars, ticks, spreads)
        )
        print(
            "Record counts:",
            bars.record_count,
            ticks.record_count,
            spreads.record_count,
        )

        # Stage 5 — Apply quality failure behavior and return typed datasets unchanged.
        _stage(5)
        remediation = tuple(
            unwrap_data_response(
                summarize_quality_remediation(report),
                operation="data.quality.summarize_quality_remediation",
                request_id=request_id,
            )
            for report in reports
        )
        print("Quality states:", tuple(report.quality_status for report in reports))
        print("Remediation summaries:", remediation)
    print("OUTPUT BOUNDARY — three typed MarketDataset values")


if __name__ == "__main__":
    main()
