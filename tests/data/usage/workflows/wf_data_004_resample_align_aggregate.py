"""WF-DATA-004: resample, align, and aggregate genuine MT5 evidence."""

from __future__ import annotations

import sys
import tempfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    generate_tick_series,
    get_market_data,
    resample_ohlcv,
    unwrap_data_response,
)
from tests.data.usage.workflows._support import isolated_runtime, market_request

WORKFLOW_ID = "WF-DATA-004"
STAGES = (
    "Retrieve ordered canonical M1 bars from MT5.",
    "Resample only to a supported higher timeframe.",
    "Backward-align only values available at target timestamps.",
    "Aggregate canonical generated ticks with an explicit price policy.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute the deterministic transformation workflow."""
    print(f"{WORKFLOW_ID} — Resample, Align, and Aggregate")
    print("INPUT BOUNDARY — normalized genuine MT5 bars")

    with tempfile.TemporaryDirectory(prefix="wf-data-004-") as directory:
        root = Path(directory)
        with isolated_runtime(root):
            # Stage 1 — Retrieve ordered canonical M1 bars from MT5.
            _stage(1)
            minute_resp = get_market_data(
                market_request("bars", timeframe="M1", limit=30)
            )
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
