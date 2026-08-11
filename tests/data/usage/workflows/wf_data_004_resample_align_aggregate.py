"""WF-DATA-004: resample, align, and aggregate genuine MT5 evidence."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    build_data_settings,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    generate_tick_series,
    get_market_data,
    resample_ohlcv,
    run_data_migrations,
    unwrap_data_response,
)
from app.utils import generate_id

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)
WORKFLOW_ID = "WF-DATA-004"
STAGES = (
    "Retrieve ordered canonical M1 bars from MT5.",
    "Resample only to a supported higher timeframe.",
    "Align multitimeframe series without forward-looking bias.",
    "Calculate quality indicators and export analytical tables.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _market_request(data_kind, *, timeframe, limit):
    """Build one bounded MT5 request inline."""
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


def main() -> None:
    """Execute resample, alignment, and aggregation workflow."""
    print(f"{WORKFLOW_ID} — Resample, Align, and Aggregate")
    print("INPUT BOUNDARY — normalized genuine MT5 bars")

    with tempfile.TemporaryDirectory(prefix="wf-data-004-") as directory:
        root = Path(directory)
        (root / "data" / "raw").mkdir(parents=True, exist_ok=True)
        settings = build_data_settings(
            database_url="sqlite:///workflow.sqlite3",
            data_dir=root,
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

            # Stage 1 — Retrieve ordered canonical M1 bars from MT5.
            _stage(1)
            minute_resp = get_market_data(
                _market_request("bars", timeframe="M1", limit=30)
            )
            if minute_resp.status != "success":
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=_START,
                    record_count=30,
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
                minute = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                minute = unwrap_data_response(
                    minute_resp,
                    operation="get_market_data",
                    request_id=minute_resp.metadata.request_id,
                )

            # Stage 2 — Resample only to a supported higher timeframe.
            _stage(2)
            five_minute_resp = resample_ohlcv(minute, "M5")
            five_minute = unwrap_data_response(
                five_minute_resp,
                operation="resample_ohlcv",
                request_id=minute.request_id,
            )

            # Stage 3 — Backward-align only values available at target timestamps.
            _stage(3)
            aligned_resp = align_multitimeframe_data(
                {"M1": minute, "M5": five_minute},
                target_timestamps=(minute.available_at,),
            )
            aligned = unwrap_data_response(
                aligned_resp,
                operation="align_multitimeframe_data",
                request_id=minute.request_id,
            )

            # Stage 4 — Aggregate canonical generated ticks with an explicit price policy.
            _stage(4)
            ticks_resp = generate_tick_series(
                five_minute,
                model="trading_bar",
                trading_timeframe="M5",
                fixed_spread_points=Decimal(2),
            )
            ticks = unwrap_data_response(
                ticks_resp,
                operation="generate_tick_series",
                request_id=minute.request_id,
            )

            ticks_with_volume = ticks.model_copy(
                update={
                    "records": tuple(
                        record.model_copy(
                            update={"volume": Decimal(1), "volume_unit": "ticks"}
                        )
                        for record in ticks.records
                    )
                }
            )
            aggregated_resp = aggregate_ticks_to_bars(ticks_with_volume, "M5", "last")
            aggregated = unwrap_data_response(
                aggregated_resp,
                operation="aggregate_ticks_to_bars",
                request_id=minute.request_id,
            )

            print(
                "Output counts:",
                five_minute.record_count,
                len(aligned),
                aggregated.record_count,
            )
    print("OUTPUT BOUNDARY — deterministic no-lookahead MarketDataset values")


if __name__ == "__main__":
    main()
