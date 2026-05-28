"""Usage example for running a vectorized HaruQuant strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.strategy import register_builtin_strategy_tools, run_vectorized_strategy


def main() -> None:
    """Run the built-in trend-following strategy on sample OHLC data."""
    register_builtin_strategy_tools(request_id="usage-strategy-registry-001")
    rows = []
    close = 1.1000
    for index in range(260):
        close = close + (0.0004 if index > 130 else -0.0001)
        rows.append(
            {
                "open": close,
                "high": close + 0.0003,
                "low": close - 0.0003,
                "close": close,
            }
        )
    data = pd.DataFrame(rows)
    result = run_vectorized_strategy(
        "TrendFollowingStrategy",
        data,
        params={
            "symbol": "EURUSD",
            "fast_period": 5,
            "slow_period": 10,
            "filter_period": 20,
        },
        request_id="usage-run-vectorized-001",
    )
    if result["status"] == "success":
        print(f"Signals: {len(result['data']['signals'])}")
    else:
        print(result["error"])


if __name__ == "__main__":
    main()
