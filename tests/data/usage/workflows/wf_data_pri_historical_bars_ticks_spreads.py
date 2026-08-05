"""WF-DATA-PRI: retrieve historical MT5 bars, ticks, and spreads."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_market_data_request,
    data_settings_context,
    ensure_source,
    evaluate_source_policy,
    get_market_data,
    get_spread_data,
    get_tick_data,
    inspect_dataset_quality,
    run_data_migrations,
    summarize_quality_remediation,
    to_ohlcv_dataframe,
    to_tick_dataframe,
    unwrap_data_response,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-PRI"
STAGES = (
    "Validate request bounds, UTC range, workflow context, precision, stale policy, and fallback list.",
    "Compose MT5 and enforce readiness, capability, license, rate, timeout, and breaker policy.",
    "Resolve cache identity and apply the explicit stale-cache policy.",
    "Fetch bounded observations, normalize them, and inspect measured quality.",
    "Apply quality failure behavior and return typed datasets unchanged.",
)

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)


def _market_request(data_kind: str, *, timeframe: str | None, limit: int) -> object:
    """Build one bounded genuine MT5 request inline."""
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,  # type: ignore[arg-type]
        timeframe=timeframe if data_kind == "bars" else None,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
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

    with tempfile.TemporaryDirectory(prefix="wf-data-pri-") as directory:
        (Path(directory) / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///workflow.sqlite3",
            data_dir=Path(directory),
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(
                Path("raw"),
                Path("processed"),
                Path("data"),
                Path("data/raw"),
                Path("data/processed"),
            ),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            request_id = generate_id("req")

            # Stage 1 — Validate request bounds, UTC range, workflow context, precision, stale policy, and fallback list.
            _stage(1)
            bars_request = _market_request("bars", timeframe="M1", limit=20)
            ticks_request = _market_request("ticks", timeframe=None, limit=20)
            spreads_request = _market_request("spreads", timeframe=None, limit=20)
            print("Validated request IDs:", bars_request.request_id)  # type: ignore[attr-defined]

            # Stage 2 — Compose MT5 and enforce readiness, capability, license, rate, timeout, and breaker policy.
            _stage(2)
            ensure_resp = ensure_source("mt5", bars_request.request_id)  # type: ignore[arg-type]
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
            assert bars_request.use_cache is False  # type: ignore[attr-defined]
            assert bars_request.stale_cache_policy == "refresh"  # type: ignore[attr-defined]
            print(
                "Cache policy:",
                bars_request.use_cache,  # type: ignore[attr-defined]
                bars_request.stale_cache_policy,  # type: ignore[attr-defined]
            )

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
            bars_df = unwrap_data_response(
                to_ohlcv_dataframe(bars),
                operation="to_ohlcv_dataframe",
                request_id=request_id,
            )
            ticks_df = unwrap_data_response(
                to_tick_dataframe(ticks),
                operation="to_tick_dataframe",
                request_id=request_id,
            )
            spreads_df = pd.DataFrame([r.model_dump() for r in spreads.records])
            print("Bars DataFrame:\n", bars_df)
            print("Ticks DataFrame:\n", ticks_df)
            print("Spreads DataFrame:\n", spreads_df)

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
            print("\nQuality Scores:", [report.quality_score for report in reports])
            print(
                "\nQuality Status:", tuple(report.quality_status for report in reports)
            )
            print("\nRemediation Summaries:", remediation)
    print("\nOUTPUT BOUNDARY — three typed MarketDataset values")


if __name__ == "__main__":
    main()
