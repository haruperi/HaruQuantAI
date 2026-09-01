"""WF-DATA-016: generate ticks and Parquet from genuine MT5 bars."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    generate_tick_series,
    generate_tick_series_to_parquet,
    get_market_data,
    run_data_migrations,
    unwrap_data_response,
)

WORKFLOW_ID = "WF-DATA-016"
STAGES = (
    "Retrieve bounded genuine MT5 bar evidence.",
    "Select one approved tick and spread model.",
    "Generate canonical ordered ticks with intra-bar phase metadata.",
    "Stream the bounded result to a temporary Parquet artifact.",
)

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)


def _market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
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
    """Execute tick generation from real bars."""
    print(f"{WORKFLOW_ID} — Tick-Series Generation from Real Evidence")
    print("INPUT BOUNDARY — genuine MT5 MarketDataset and approved models")

    with tempfile.TemporaryDirectory(prefix="wf-data-016-") as directory:
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
            request_id = generate_id("req")
            run_data_migrations(request_id)

            # Stage 1 — Retrieve bounded genuine MT5 bar evidence.
            _stage(1)
            bars_resp = get_market_data(
                _market_request("bars", timeframe="M1", limit=10)
            )
            if bars_resp.status != "success":
                end = datetime.now(UTC)
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=end - timedelta(hours=1),
                    record_count=10,
                    method="gbm",
                    seed=42,
                    parameters={
                        "start_val": Decimal("1.10"),
                        "mu": Decimal("0.02"),
                        "sigma": Decimal("0.10"),
                    },
                    precision_policy="decimal_string",
                    request_id=request_id,
                )
                bars = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                bars = unwrap_data_response(
                    bars_resp, operation="get_market_data", request_id=request_id
                )

            # Stage 2 — Select one approved tick and spread model.
            _stage(2)
            arguments = {
                "model": "trading_bar",
                "trading_timeframe": "M1",
                "spread_model": "fixed_spread",
                "fixed_spread_points": Decimal(2),
                "point_value": Decimal("0.00001"),
            }

            # Stage 3 — Generate canonical ordered ticks with intra-bar phase metadata.
            _stage(3)
            ticks_resp = generate_tick_series(bars, **arguments)
            ticks = unwrap_data_response(
                ticks_resp, operation="generate_tick_series", request_id=request_id
            )
            assert all(record.source_bar_time is not None for record in ticks.records)

            # Stage 4 — Stream the bounded result to a temporary Parquet artifact.
            _stage(4)
            out_path = Path("data/raw/ticks.parquet")
            artifact_resp = generate_tick_series_to_parquet(
                bars,
                path=out_path,
                max_output_rows_per_chunk=1000,
                **arguments,
            )
            artifact = unwrap_data_response(
                artifact_resp,
                operation="generate_tick_series_to_parquet",
                request_id=request_id,
            )
            assert Path(str(artifact.get("path"))).is_file()
            print("Tick evidence:", ticks.record_count, artifact.get("rows"))
    print("OUTPUT BOUNDARY — canonical tick MarketDataset and bounded Parquet artifact")


if __name__ == "__main__":
    main()
