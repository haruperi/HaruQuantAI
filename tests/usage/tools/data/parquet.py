"""Usage example for HaruQuantAI Parquet data tools.

Run from the project root after installing the project dependencies:

    python tests/usage/tools/data/parquet.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.data import (
    parquet_data_load,
    parquet_data_saver_file_exists,
    parquet_data_saver_load,
    parquet_data_saver_save,
)

REQUEST_ID = "usage-parquet-001"


def _create_sample_parquet(path: Path) -> None:
    """Create a small local Parquet file for the usage example."""

    frame = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=5, freq="h"),
            "open": [1.1000, 1.1010, 1.1020, 1.1030, 1.1040],
            "high": [1.1020, 1.1030, 1.1040, 1.1050, 1.1060],
            "low": [1.0990, 1.1000, 1.1010, 1.1020, 1.1030],
            "close": [1.1010, 1.1020, 1.1030, 1.1040, 1.1050],
            "volume": [100, 110, 120, 130, 140],
            "spread": [10, 11, 10, 12, 11],
        }
    )
    frame.to_parquet(path)


def _print_result(label: str, result: dict) -> None:
    """Print a compact success/error summary for a tool result."""

    if result["status"] == "success":
        print(f"{label}: success")
        print(result["data"])
    else:
        print(f"{label}: error")
        print(result["error"])


def main() -> None:
    """Run a simple Parquet data workflow."""

    workflow_dir = Path(tempfile.mkdtemp(prefix="haruquant-parquet-"))
    sample_path = workflow_dir / "sample_usage_eurusd_h1.parquet"
    saved_path = workflow_dir / "EURUSD_H1.parquet"
    _create_sample_parquet(sample_path)

    load_result = parquet_data_load(sample_path, request_id=REQUEST_ID)
    _print_result("load parquet", load_result)

    exists_result = parquet_data_saver_file_exists(
        path=sample_path,
        request_id=REQUEST_ID,
    )
    _print_result("check parquet exists", exists_result)

    save_result = parquet_data_saver_save(
        data=load_result["data"] if load_result["status"] == "success" else None,
        path=saved_path,
        is_initial=True,
        request_id=REQUEST_ID,
    )
    _print_result("save parquet artifact", save_result)

    saved_load_result = parquet_data_saver_load(
        path=saved_path,
        symbol="EURUSD",
        timeframe="H1",
        request_id=REQUEST_ID,
    )
    _print_result("load saved parquet artifact", saved_load_result)


if __name__ == "__main__":
    main()
