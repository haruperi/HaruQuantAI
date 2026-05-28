"""Usage example for scheduled data updater tools."""

from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from tools.data import (
    scheduled_data_updater_create,
    scheduled_data_updater_run_once,
    scheduled_data_updater_status,
    scheduled_data_updater_stop,
)
from tools.data.scheduler import register_scheduled_update_function


def _payload(values: list[float], start: str = "2024-01-01") -> dict:
    """Create a JSON-safe OHLCV payload for the example."""

    frame = pd.DataFrame(
        {
            "open": values,
            "high": values,
            "low": values,
            "close": values,
            "volume": [100] * len(values),
        },
        index=pd.date_range(start, periods=len(values), freq="D"),
    )
    return {
        "symbol": "EURUSD",
        "timeframe": "D1",
        "data": [
            {"timestamp": idx.isoformat(), **row.to_dict()}
            for idx, row in frame.iterrows()
        ],
    }


def refresh_data(_current_data):
    """Example approved updater function."""

    return _payload([3.0], start="2024-01-03")


def main() -> None:
    """Create an updater, run one cycle, inspect status, then stop it."""

    register_scheduled_update_function("example_refresh", refresh_data, replace=True)

    created = scheduled_data_updater_create(
        data=_payload([1.0, 2.0]),
        update_func_name="example_refresh",
        interval_sec=60,
        request_id="usage-scheduler-001",
    )
    if created["status"] != "success":
        print(created["error"])
        return

    state_id = created["data"]["state_id"]
    update_result = scheduled_data_updater_run_once(
        state_id,
        request_id="usage-scheduler-002",
    )
    status_result = scheduled_data_updater_status(
        state_id,
        request_id="usage-scheduler-003",
    )
    stop_result = scheduled_data_updater_stop(
        state_id,
        request_id="usage-scheduler-004",
    )

    print(update_result["data"])
    print(status_result["data"])
    print(stop_result["data"])


if __name__ == "__main__":
    main()
