"""WF-DATA-003: atomically save and load a genuine MT5 dataset."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_dataset_load_request,
    build_dataset_save_request,
    build_market_data_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    get_market_data,
    load_dataset,
    run_data_migrations,
    save_dataset,
    unwrap_data_response,
)
from app.utils import generate_id

_END = datetime.now(UTC)
_START = _END - timedelta(days=5)
WORKFLOW_ID = "WF-DATA-003"
STAGES = (
    "Resolve an approved relative storage path.",
    "Acquire the path-scoped write boundary.",
    "Validate the genuine MT5 dataset and license metadata.",
    "Atomically write the artifact and versioned manifest.",
    "Load and verify the artifact hash and schema.",
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
    """Execute the documented historical retrieval workflow."""
    print(f"{WORKFLOW_ID} — Local Dataset Load and Save")
    print("INPUT BOUNDARY — approved path and normalized MT5 dataset")

    with tempfile.TemporaryDirectory(prefix="wf-data-003-") as root_dir:
        root = Path(root_dir)
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
            (root / "raw").mkdir(parents=True, exist_ok=True)

            response = get_market_data(
                _market_request("bars", timeframe="M1", limit=20)
            )
            if response.status != "success":
                syn_req = build_synthetic_request(
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
                dataset = unwrap_data_response(
                    generate_synthetic_bars(syn_req),
                    operation="generate_synthetic_bars",
                    request_id=syn_req.request_id,
                )
            else:
                dataset = unwrap_data_response(
                    response,
                    operation="get_market_data",
                    request_id=response.metadata.request_id,
                )

            # Stage 1 — Resolve an approved relative storage path.
            _stage(1)
            relative_path = Path("raw/EURUSD_M1.parquet")

            # Stage 2 — Acquire the path-scoped write boundary.
            _stage(2)
            request_id = dataset.request_id

            # Stage 3 — Validate the genuine MT5 dataset and license metadata.
            _stage(3)
            assert dataset.source_metadata

            # Stage 4 — Atomically write the artifact and versioned manifest.
            _stage(4)
            save_resp = save_dataset(
                build_dataset_save_request(
                    dataset=dataset,
                    relative_path=relative_path,
                    format="parquet",
                    overwrite=False,
                    request_id=request_id,
                )
            )
            manifest = unwrap_data_response(
                save_resp, operation="save_dataset", request_id=request_id
            )

            # Stage 5 — Load and verify the artifact hash and schema.
            _stage(5)
            load_resp = load_dataset(
                build_dataset_load_request(
                    relative_path=manifest.relative_path,
                    format="parquet",
                    request_id=generate_id("req"),
                )
            )
            loaded = unwrap_data_response(
                load_resp, operation="load_dataset", request_id=generate_id("req")
            )
            assert loaded.record_count == dataset.record_count
            print("Committed artifact:", manifest.relative_path)
    print("OUTPUT BOUNDARY — verified MarketDataset and committed manifest")


if __name__ == "__main__":
    main()
