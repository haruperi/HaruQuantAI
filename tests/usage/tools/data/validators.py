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

from tools.data import validate_ohlcv_quality

df = pd.DataFrame(
    {
        "time": pd.date_range("2026-01-01", periods=100, freq="h", tz="UTC"),
        "open": [1.10 + i * 0.001 for i in range(100)],
        "high": [1.11 + i * 0.001 for i in range(100)],
        "low": [1.09 + i * 0.001 for i in range(100)],
        "close": [1.105 + i * 0.001 for i in range(100)],
        "volume": [100 + i for i in range(100)],
        "spread": [1.2 for _ in range(100)],
    }
)
result = validate_ohlcv_quality(
    df,
    profile="backtest",
    expected_frequency="1h",
    minimum_rows=50,
    request_id="usage-data-validator-001",
)
print(result["data"]["decision"] if result["status"] == "success" else result["error"])
