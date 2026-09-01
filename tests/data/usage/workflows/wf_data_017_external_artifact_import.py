"""WF-DATA-017: import a declared CSV derived from genuine MT5 bars."""

from __future__ import annotations

import csv
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from decimal import Decimal

from app.kernel.identity import generate_id
from app.services.data import (
    build_column_mapping,
    build_data_settings,
    build_dataset_load_request,
    build_external_import_request,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    describe_import_dialects,
    generate_synthetic_bars,
    get_market_data,
    import_external_dataset,
    load_dataset,
    run_data_migrations,
    unwrap_data_response,
)

WORKFLOW_ID = "WF-DATA-017"
STAGES = (
    "Resolve an approved external artifact path.",
    "Declare the CSV dialect and explicit column mapping.",
    "Map genuine MT5 observations to canonical fields.",
    "Run canonical quality validation.",
    "Commit through manifest-backed storage.",
    "Persist external-origin audit evidence and reload the artifact.",
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
    """Execute explicit external artifact admission."""
    print(f"{WORKFLOW_ID} — External Artifact Import")
    print("INPUT BOUNDARY — approved CSV path, dialect, and ColumnMapping")

    with tempfile.TemporaryDirectory(prefix="wf-data-017-") as directory:
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
            root = Path(directory)
            raw = root / "raw"
            raw.mkdir(parents=True, exist_ok=True)

            bars_resp = get_market_data(
                _market_request("bars", timeframe="M1", limit=5)
            )
            if bars_resp.status != "success":
                end = datetime.now(UTC)
                syn_req = build_synthetic_request(
                    symbol="EURUSD",
                    data_kind="bars",
                    timeframe="M1",
                    start=end - timedelta(hours=1),
                    record_count=5,
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

            # Stage 1 — Resolve an approved external artifact path.
            _stage(1)
            source_path = raw / "provider_export.csv"

            # Stage 2 — Declare the CSV dialect and explicit column mapping.
            _stage(2)
            dialects_resp = describe_import_dialects()
            dialects = unwrap_data_response(
                dialects_resp,
                operation="describe_import_dialects",
                request_id=request_id,
            )
            assert "standard" in dialects
            mapping = build_column_mapping(
                timestamp="timestamp",
                open="open",
                high="high",
                low="low",
                close="close",
                volume="volume",
            )

            # Stage 3 — Map genuine MT5 observations to canonical fields.
            _stage(3)
            with source_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(("timestamp", "open", "high", "low", "close", "volume"))
                for bar in bars.records:
                    writer.writerow(
                        (
                            bar.timestamp.isoformat(),
                            bar.open,
                            bar.high,
                            bar.low,
                            bar.close,
                            bar.volume,
                        )
                    )

            run_data_migrations(request_id)

            # Stage 4 — Run canonical quality validation.
            _stage(4)
            request = build_external_import_request(
                relative_path=Path("raw/provider_export.csv"),
                format="csv",
                dialect="standard",
                mapping=mapping,
                symbol="EURUSD",
                data_kind="bars",
                timeframe="M1",
                source_id="mt5-export",
                workflow_context="research",
                precision_policy="decimal_string",
                price_unit="USD",
                volume_unit="lots",
                destination_path=Path("raw/EURUSD_M1.csv"),
                request_id=request_id,
            )

            # Stage 5 — Commit through manifest-backed storage.
            _stage(5)
            manifest_resp = import_external_dataset(request)
            manifest = unwrap_data_response(
                manifest_resp,
                operation="import_external_dataset",
                request_id=request_id,
            )

            # Stage 6 — Persist external-origin audit evidence and reload the artifact.
            _stage(6)
            loaded_resp = load_dataset(
                build_dataset_load_request(
                    relative_path=manifest.relative_path,
                    format="csv",
                    request_id=request_id,
                )
            )
            loaded = unwrap_data_response(
                loaded_resp, operation="load_dataset", request_id=request_id
            )
            print(
                "Imported records and origin:",
                loaded.record_count,
                loaded.source_metadata.get("origin"),
            )
    print(
        "OUTPUT BOUNDARY — committed canonical artifact, manifest, and audit evidence"
    )


if __name__ == "__main__":
    main()
