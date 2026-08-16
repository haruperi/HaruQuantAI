"""WF-DATA-PRI: retrieve historical MT5 bars, ticks, and spreads."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    ensure_source,
    evaluate_source_policy,
    generate_synthetic_bars,
    generate_synthetic_ticks,
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
    """Build one bounded synthetic request inline."""
    return build_market_data_request(
        source_id="synthetic",
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


def main() -> None:  # noqa: PLR0915
    """Execute the documented historical retrieval workflow."""
    print("INPUT BOUNDARY — bounded EURUSD UTC requests and typed Data settings")
    print(f"{WORKFLOW_ID} — Historical Bars, Ticks, and Spreads")
    with tempfile.TemporaryDirectory(prefix="wf-data-pri-") as directory:
        raw_dir = Path(directory) / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "symbols.json").write_text(
            '{"EURUSD": {"asset_class": "forex", "revision": "v1", "retrieved_at": "2026-01-01T00:00:00Z"}}'
        )
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
            data_local_sources=("synthetic",),
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
            ensure_source("synthetic", bars_request.request_id)  # type: ignore[arg-type]
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
            bars_resp = get_market_data(bars_request)
            if bars_resp.status != "success":
                syn_b_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=_START,
                    record_count=20,
                    method="gbm",
                    seed=42,
                    parameters={
                        "start_val": Decimal("1.10"),
                        "mu": Decimal("0.02"),
                        "sigma": Decimal("0.10"),
                    },
                    precision_policy="decimal_string",
                    request_id=generate_id("req"),
                )
                bars = unwrap_data_response(
                    generate_synthetic_bars(syn_b_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_b_req.request_id,
                )
                syn_t_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="ticks",
                    timeframe=None,
                    start=_START,
                    record_count=20,
                    method="gbm",
                    seed=42,
                    parameters={
                        "start_val": Decimal("1.10"),
                        "mu": Decimal("0.02"),
                        "sigma": Decimal("0.10"),
                    },
                    precision_policy="decimal_string",
                    request_id=generate_id("req"),
                )
                ticks = unwrap_data_response(
                    generate_synthetic_ticks(syn_t_req),
                    operation="generate_synthetic_ticks",
                    request_id=syn_t_req.request_id,
                )
                spreads = bars
            else:
                bars = unwrap_data_response(
                    bars_resp,
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
            bars_df = to_ohlcv_dataframe(bars)
            ticks_df = to_tick_dataframe(ticks)
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
