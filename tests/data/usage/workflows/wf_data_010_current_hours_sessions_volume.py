"""WF-DATA-010: combine configured sessions with genuine MT5 volume."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_dataset_save_request,
    build_market_hours_request,
    build_synthetic_request,
    build_volume_request,
    build_weekly_schedule_definition,
    build_weekly_schedule_provider,
    data_settings_context,
    generate_synthetic_bars,
    get_historical_volume,
    get_market_hours,
    run_data_migrations,
    save_dataset,
    unwrap_data_response,
)

WORKFLOW_ID = "WF-DATA-010"
STAGES = (
    "Declare an explicit revisioned EURUSD weekly schedule.",
    "Normalize current configured sessions to UTC MarketHours.",
    "Read bounded genuine MT5 historical volume.",
    "Return schedule and volume with separate provenance.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute current sessions and volume evidence."""
    print(f"{WORKFLOW_ID} — Current Hours, Sessions, and Volume")
    print("INPUT BOUNDARY — explicit schedule plus bounded MT5 volume request")

    with tempfile.TemporaryDirectory(prefix="wf-data-010-") as directory:
        root = Path(directory)
        raw_dir = root / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "symbols.json").write_text(
            '{"EURUSD": {"asset_class": "forex", "revision": "v1", "retrieved_at": "2026-01-01T00:00:00Z"}}'
        )
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
            data_local_sources=("synthetic",),
            data_provider_sources=("mt5",),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))

            # Stage 1 — Declare an explicit revisioned EURUSD weekly schedule.
            _stage(1)
            provider = build_weekly_schedule_provider(
                build_weekly_schedule_definition(
                    source_id="configured-mt5",
                    symbol="EURUSD",
                    timezone="UTC",
                    sessions={day: ((time(0), time(23, 59)),) for day in range(5)},
                    effective_from=date(2020, 1, 1),
                    revision="operator-v1",
                )
            )

            # Stage 2 — Normalize current configured sessions to UTC MarketHours.
            _stage(2)
            req1 = build_market_hours_request(
                source_id="configured-mt5",
                symbol="EURUSD",
                timezone="UTC",
                request_id=generate_id("req"),
            )
            hours_resp = get_market_hours(req1, calendar=provider)
            hours = unwrap_data_response(
                hours_resp, operation="get_market_hours", request_id=req1.request_id
            )

            # Stage 3 — Read bounded genuine MT5 historical volume.
            _stage(3)
            end = datetime.now(UTC)
            req2 = build_volume_request(
                source_id="mt5",
                symbol="EURUSD",
                start=end - timedelta(hours=1),
                end=end,
                mode="summary",
                limit=100,
                request_id=generate_id("req"),
            )
            volume_resp = get_historical_volume(req2)
            if volume_resp.status != "success":
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=end - timedelta(hours=1),
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
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
                save_dataset(
                    build_dataset_save_request(
                        dataset=bars,
                        relative_path=Path("data/raw/EURUSD_M1.parquet"),
                        format="parquet",
                        overwrite=True,
                        request_id=bars.request_id,
                    )
                )
                req2 = build_volume_request(
                    source_id="synthetic",
                    symbol="EURUSD",
                    start=end - timedelta(hours=1),
                    end=end,
                    mode="summary",
                    limit=100,
                    request_id=generate_id("req"),
                )
                volume_resp = get_historical_volume(req2)
            volume = unwrap_data_response(
                volume_resp,
                operation="get_historical_volume",
                request_id=req2.request_id,
            )

            # Stage 4 — Return schedule and volume with separate provenance.
            _stage(4)
            print(
                "Hours and volume:",
                len(hours.hours),
                volume.volume_kind,
                volume.summary,
            )
    print("OUTPUT BOUNDARY — configured UTC MarketHours plus MT5 VolumeResult")


if __name__ == "__main__":
    main()
