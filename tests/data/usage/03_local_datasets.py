"""Demonstrate FEAT-DATA-03 local-dataset loading operations across CSV and Parquet formats."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataError
from app.services.data.local_datasets import (
    DatasetLoadRequest,
    load_csv,
    load_dataset,
    load_local_dataset,
    load_parquet,
)
from app.utils import generate_id


def example_08_csv_load_direct() -> None:
    """Load a local CSV file directly via load_csv."""
    with TemporaryDirectory(prefix="haru-local-csv-") as tmpdir:
        sample_path = Path(tmpdir) / "EURUSD_M1.csv"
        sample_path.write_text(
            "timestamp,open,high,low,close,volume\n"
            "2026-07-01T12:00:00Z,1.1000,1.1020,1.0990,1.1010,100\n"
            "2026-07-01T12:01:00Z,1.1010,1.1025,1.1005,1.1015,120\n",
            encoding="utf-8",
        )
        try:
            ds = load_csv(sample_path)
            print(f"Loaded CSV direct rows: {ds.record_count}")
        except DataError as exc:
            print(f"CSV direct load error handled: {exc.code}")


def example_10_csv_fetch_range() -> None:
    """Fetch a range from a local CSV file via DatasetLoadRequest and load_local_dataset."""
    req_id = generate_id("req")
    request = DatasetLoadRequest(
        relative_path=Path("usage/example.csv"),
        format="csv",
        request_id=req_id,
    )
    try:
        ds = load_local_dataset(request)
        print(f"Loaded CSV range dataset: symbol={ds.symbol} rows={ds.record_count}")
    except DataError as exc:
        print(f"CSV range fetch handled: {exc.code}")


def example_11_parquet_load_direct() -> None:
    """Load a local Parquet file directly via load_parquet."""
    with TemporaryDirectory(prefix="haru-local-parquet-") as tmpdir:
        sample_path = Path(tmpdir) / "EURUSD_M1.parquet"
        try:
            ds = load_parquet(sample_path)
            print(f"Loaded Parquet direct rows: {ds.record_count}")
        except DataError as exc:
            print(f"Parquet direct load error handled: {exc.code}")


def main() -> None:
    """Run all local dataset loading examples."""
    example_08_csv_load_direct()
    example_10_csv_fetch_range()
    example_11_parquet_load_direct()


if __name__ == "__main__":
    main()
