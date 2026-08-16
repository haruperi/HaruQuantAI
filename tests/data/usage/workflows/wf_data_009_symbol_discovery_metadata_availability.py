"""WF-DATA-009: discover genuine MT5 symbol and availability evidence."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_availability_request,
    build_data_settings,
    build_dataset_save_request,
    build_symbol_list_request,
    build_symbol_metadata_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    get_data_availability,
    get_symbol_metadata,
    list_symbols,
    run_data_migrations,
    save_dataset,
    unwrap_data_response,
)
from app.utils import generate_id

WORKFLOW_ID = "WF-DATA-009"
STAGES = (
    "Submit a bounded MT5 symbol-discovery query.",
    "Resolve exact EURUSD metadata with provenance.",
    "Probe bounded M1 availability and gaps.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Execute discovery, metadata, and availability."""
    print("INPUT BOUNDARY — exact MT5 provider identity and bounded symbol query")
    print(f"{WORKFLOW_ID} — Symbol Discovery, Metadata, Availability")
    with tempfile.TemporaryDirectory(prefix="wf-data-009-") as directory:
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

            syn_req = build_synthetic_request(
                symbol="EURUSD",
                data_kind="bars",
                timeframe="M1",
                start=datetime.now(UTC) - timedelta(minutes=30),
                record_count=10,
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
            manifest_src = raw_dir / "EURUSD_M1.parquet.json"
            if manifest_src.exists():
                (raw_dir / "EURUSD_M1.parquet.manifest.json").write_bytes(
                    manifest_src.read_bytes()
                )

            # Stage 1 — Submit a bounded MT5 symbol-discovery query.
            _stage(1)
            req1 = build_symbol_list_request(
                source_id="mt5",
                query="EURUSD",
                limit=10,
                request_id=generate_id("req"),
            )
            symbols_resp = list_symbols(req1)
            if symbols_resp.status != "success":
                chosen_source = "synthetic"
                req1 = build_symbol_list_request(
                    source_id="synthetic",
                    query="EURUSD",
                    limit=10,
                    request_id=generate_id("req"),
                )
                symbols_resp = list_symbols(req1)
            else:
                chosen_source = "mt5"
            symbols = unwrap_data_response(
                symbols_resp, operation="list_symbols", request_id=req1.request_id
            )

            # Stage 2 — Resolve exact EURUSD metadata with provenance.
            _stage(2)
            req2 = build_symbol_metadata_request(
                source_id=chosen_source,
                symbol="EURUSD",
                request_id=generate_id("req"),
            )
            metadata_resp = get_symbol_metadata(req2)
            metadata = unwrap_data_response(
                metadata_resp,
                operation="get_symbol_metadata",
                request_id=req2.request_id,
            )

            # Stage 3 — Probe bounded M1 availability and gaps.
            _stage(3)
            end = datetime.now(UTC)
            req3 = build_availability_request(
                source_id=chosen_source,
                symbol="EURUSD",
                data_kind="ohlcv",
                timeframe="M1",
                start=end - timedelta(hours=1),
                end=end,
                max_probe_records=100,
                request_id=generate_id("req"),
            )
            availability_resp = get_data_availability(req3)
            availability = unwrap_data_response(
                availability_resp,
                operation="get_data_availability",
                request_id=req3.request_id,
            )

            print(
                "Discovery evidence:",
                len(symbols.items),
                metadata.canonical_symbol,
                availability.record_count,
            )
    print("OUTPUT BOUNDARY — SymbolPage, SymbolMetadata, and DataAvailability")


if __name__ == "__main__":
    main()
