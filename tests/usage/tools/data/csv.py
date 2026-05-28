"""Usage example for HaruQuantAI CSV data tools.

Run from the project root after installing project dependencies:

    python tests/usage/tools/data/csv.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.data import (
    csv_data_fetch_range,
    csv_data_load,
    csv_data_saver_file_exists,
    csv_data_saver_load,
    csv_data_saver_save,
)

REQUEST_ID = "usage-csv-data-001"
SAMPLE_CSV = Path("tests/fixtures/data/sample_ohlcvs.csv")


def print_result(label: str, result: dict) -> None:
    """Print a compact success/error summary for a tool response."""

    print(f"\n[{label}] {result['status'].upper()}: {result['message']}")
    if result["status"] == "success":
        data = result.get("data") or {}
        print(f"metadata={result['metadata']}")
        if "rows" in data:
            print(f"rows={data['rows']} columns={data.get('columns')}")
        else:
            print(f"data={data}")
    else:
        print(f"error={result['error']}")


def main() -> None:
    """Demonstrate a simple CSV load, slice, save, exists, and reload workflow."""

    saved_csv = Path(tempfile.mkdtemp(prefix="haruquant-csv-")) / "EURUSD_M1.csv"

    load_result = csv_data_load(
        SAMPLE_CSV,
        index_col=None,
        request_id=REQUEST_ID,
    )
    print_result("load csv", load_result)

    range_result = csv_data_fetch_range(
        SAMPLE_CSV,
        symbol="EURUSD",
        timeframe="M1",
        start_pos=0,
        end_pos=10,
        request_id=REQUEST_ID,
        cache=True,
    )
    print_result("fetch range", range_result)

    if load_result["status"] == "success":
        save_result = csv_data_saver_save(
            load_result["data"],
            path=saved_csv,
            is_initial=True,
            request_id=REQUEST_ID,
        )
        print_result("save csv", save_result)

    exists_result = csv_data_saver_file_exists(
        path=saved_csv,
        symbol="EURUSD",
        timeframe="M1",
        request_id=REQUEST_ID,
    )
    print_result("file exists", exists_result)

    saved_load_result = csv_data_saver_load(
        path=saved_csv,
        symbol="EURUSD",
        timeframe="M1",
        request_id=REQUEST_ID,
    )
    print_result("load saved csv", saved_load_result)


if __name__ == "__main__":
    main()
