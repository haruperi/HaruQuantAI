"""Usage example for HaruQuantAI synthetic data generation tools."""

from __future__ import annotations

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) in sys.path:
    sys.path.remove(str(CURRENT_DIR))

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.data import data_generate_ticks, gbm_data_generate


def main() -> None:
    candles_result = gbm_data_generate(
        symbols="EURUSD",
        start="2024-01-01",
        count=10,
        interval="H1",
        sigma=0.002,
        start_value=1.10,
        seed=42,
        request_id="usage-generators-001",
    )

    if candles_result["status"] != "success":
        print(candles_result["error"])
        return

    import pandas as pd

    candles = pd.DataFrame(candles_result["data"]["data"])
    candles["timestamp"] = pd.to_datetime(candles["timestamp"])
    candles = candles.set_index("timestamp")

    ticks_result = data_generate_ticks(
        candles,
        model="timeframe_ticks",
        trading_timeframe="H1",
        spread_model="fixed_spread",
        fixed_spread_points=2,
        request_id="usage-generators-002",
    )

    if ticks_result["status"] == "success":
        print(f"Generated {ticks_result['data']['rows']} ticks.")
    else:
        print(ticks_result["error"])


if __name__ == "__main__":
    main()
