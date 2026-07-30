# ruff: noqa: BLE001, E402
"""Demonstrate FEAT-DATA-03 local CSV and Parquet dataset loading."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_error,
    build_dataset_load_request,
    build_dataset_save_request,
    build_synthetic_request,
    generate_synthetic_bars,
    load_csv,
    load_local_dataset,
    load_parquet,
    save_market_data,
    to_ohlcv_dataframe,
)

DataError = build_data_error

from app.services.data import (
    build_data_error,
)

DataError = build_data_error

from app.services.data import (
    build_data_error,
)

DataError = build_data_error

from app.services.data import (
    build_data_error,
)

DataError = build_data_error

from app.utils import generate_id

_CSV_PATH = Path("data/raw/EURUSD_H1.csv")
_PARQUET_PATH = Path("data/raw/EURUSD_H1.parquet")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _ensure_raw_datasets() -> None:
    """Ensure manifest-backed CSV and Parquet datasets exist in data/raw."""
    csv_manifest = _CSV_PATH.with_suffix(".csv.manifest.json")
    parquet_manifest = _PARQUET_PATH.with_suffix(".parquet.manifest.json")
    if (
        _CSV_PATH.exists()
        and csv_manifest.exists()
        and _PARQUET_PATH.exists()
        and parquet_manifest.exists()
    ):
        return

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
    dataset = generate_synthetic_bars(synth_req)
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


def example_08_csv_load_direct() -> None:
    """Load a local CSV file directly via load_csv."""
    _header("Load a local CSV file directly via load_csv.")
    _ensure_raw_datasets()
    try:
        response = load_csv(_CSV_PATH)
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(f"Loaded CSV direct rows: {ds.record_count}")
            print(to_ohlcv_dataframe(ds))
    except Exception as exc:
        print(f"CSV direct load error handled: {exc.code}")


def example_10_csv_fetch_range() -> None:
    """Fetch a local CSV range through the typed request boundary."""
    _header("Fetch a local CSV range through the typed request boundary.")
    _ensure_raw_datasets()
    req_id = generate_id("req")
    request = build_dataset_load_request(
        relative_path=_CSV_PATH,
        format="csv",
        request_id=req_id,
    )
    try:
        response = load_local_dataset(request)
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(
                f"Loaded CSV range dataset: symbol={ds.symbol} rows={ds.record_count}"
            )
            print(to_ohlcv_dataframe(ds))
    except Exception as exc:
        print(f"CSV range fetch handled: {exc.code}")


def example_11_parquet_load_direct() -> None:
    """Load a local Parquet file directly via load_parquet."""
    _header("Load a local Parquet file directly via load_parquet.")
    _ensure_raw_datasets()
    try:
        response = load_parquet(_PARQUET_PATH)
        if response.status == "success" and response.data is not None:
            ds = response.data
            print(f"Loaded Parquet direct rows: {ds.record_count}")
            print(ds)
            print(to_ohlcv_dataframe(ds))
    except Exception as exc:
        print(f"Parquet direct load error handled: {exc.code}")


def _demonstrate_feature() -> None:
    """Run all local dataset loading examples."""
    example_08_csv_load_direct()
    example_10_csv_fetch_range()
    example_11_parquet_load_direct()


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_017() -> None:
    _header("fr_data_017")
    "FR-DATA-017: Load CSV/Parquet plus manifest only from an approved root, verify hash/schema/normalization metadata, normalize records, and reject corruption without hidden migration."
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (fr_data_017,)
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
