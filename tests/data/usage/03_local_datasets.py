# ruff: noqa: BLE001
"""Demonstrate FEAT-DATA-03 local CSV and Parquet dataset loading."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_settings,
    build_dataset_load_request,
    build_dataset_save_request,
    build_synthetic_request,
    data_settings_context,
    generate_synthetic_bars,
    load_csv,
    load_local_dataset,
    load_parquet,
    run_data_migrations,
    save_market_data,
    to_ohlcv_dataframe,
)
from app.utils import generate_id

_CSV_PATH = Path("data/raw/EURUSD_H1.csv")
_PARQUET_PATH = Path("data/raw/EURUSD_H1.parquet")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _ensure_raw_datasets() -> None:
    """Ensure manifest-backed CSV and Parquet datasets exist in approved raw directory."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    req_id = generate_id("req")
    synth_req = build_synthetic_request(
        symbol="EURUSD",
        data_kind="bars",
        timeframe="H1",
        start=datetime(2026, 6, 1, tzinfo=UTC),
        record_count=24,
        method="gbm",
        seed=42,
        parameters={
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal("1.1000"),
        },
        precision_policy="decimal_string",
        request_id=req_id,
    )
    synth_res = generate_synthetic_bars(synth_req)
    if synth_res.data is None:
        raise RuntimeError("Failed to generate synthetic bars")
    dataset = synth_res.data
    save_market_data(
        build_dataset_save_request(
            dataset=dataset,
            relative_path=_CSV_PATH,
            format="csv",
            overwrite=True,
            request_id=req_id,
        )
    )
    save_market_data(
        build_dataset_save_request(
            dataset=dataset,
            relative_path=_PARQUET_PATH,
            format="parquet",
            overwrite=True,
            request_id=req_id,
        )
    )


def fr_data_016() -> None:
    """FR-DATA-016: Stage 1 — Construct DatasetLoadRequest boundary for path resolution under approved roots."""
    _header("Stage 1: Load Request Construction - Dataset Load Request (FR-DATA-016)")
    request = build_dataset_load_request(
        relative_path=_CSV_PATH,
        format="csv",
        request_id=generate_id("req"),
    )
    print(_format_result(request))
    print(
        f"Data -> DatasetLoadRequest(path={request.relative_path}, format={request.format})"
    )


def fr_data_017_csv() -> None:
    """FR-DATA-017: Stage 2 — Load a local CSV file directly via load_csv with manifest verification."""
    _header("Stage 2: Direct CSV Loading - Load CSV Dataset (FR-DATA-017)")
    _ensure_raw_datasets()
    try:
        response = load_csv(_CSV_PATH)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(
                f"Data -> MarketDataset(symbol={ds.symbol}, records={ds.record_count})"
            )
            df = to_ohlcv_dataframe(ds)
            print(f"Data -> DataFrame shape={df.shape}")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_017_parquet() -> None:
    """FR-DATA-017: Stage 3 — Load a local Parquet file directly via load_parquet with manifest verification."""
    _header("Stage 3: Direct Parquet Loading - Load Parquet Dataset (FR-DATA-017)")
    _ensure_raw_datasets()
    try:
        response = load_parquet(_PARQUET_PATH)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(
                f"Data -> MarketDataset(symbol={ds.symbol}, records={ds.record_count})"
            )
            df = to_ohlcv_dataframe(ds)
            print(f"Data -> DataFrame shape={df.shape}")
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def fr_data_017_018_governed() -> None:
    """FR-DATA-017, FR-DATA-018: Stage 4 — Fetch a local dataset through typed load_local_dataset request boundary."""
    _header(
        "Stage 4: Manifest-Verifying Governed Load - Governed Load (FR-DATA-017, FR-DATA-018)"
    )
    _ensure_raw_datasets()
    request = build_dataset_load_request(
        relative_path=_CSV_PATH,
        format="csv",
        request_id=generate_id("req"),
    )
    try:
        response = load_local_dataset(request)
        print(_format_result(response))
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(
                f"Data -> MarketDataset(symbol={ds.symbol}, records={ds.record_count})"
            )
    except Exception as exc:
        print(f"Output Result -> {type(exc).__name__} : {type(exc).__name__}")
        print(f"Data -> Exception({exc})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    with TemporaryDirectory(prefix="usage-local-data-") as directory:
        base_dir = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///usage.sqlite3",
            data_dir=base_dir,
            approved_storage_roots=(Path("data/raw"), Path("data/processed")),
            data_raw_root=Path("data/raw"),
        )
        with data_settings_context(settings):
            run_data_migrations(generate_id("req"))
            print("=" * 80)
            print("FEATURE: FEAT-DATA-03 - Local Dataset Loading")
            print(
                "PURPOSE: DatasetLoadRequest, manifest verification, CSV/Parquet loaders, and load_local_dataset"
            )
            print(
                "MODULE FLOW: Stage 1 (Load Request Construction) -> Stage 2 (Direct CSV Loading) -> Stage 3 (Direct Parquet Loading) -> Stage 4 (Manifest-Verifying Governed Load)"
            )
            print("=" * 80)

            fr_data_016()
            fr_data_017_csv()
            fr_data_017_parquet()
            fr_data_017_018_governed()


if __name__ == "__main__":
    main()
