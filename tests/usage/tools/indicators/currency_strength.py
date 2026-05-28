"""Usage example for currency strength indicator tools."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.indicators import calculate_currency_strength, get_top_pairs


def make_pair(multiplier: float) -> pd.DataFrame:
    """Create simple pair data for examples."""
    closes = pd.Series([1.10, 1.11, 1.12, 1.13, 1.14]) * multiplier
    return pd.DataFrame(
        {
            "open": closes.shift(1).fillna(closes.iloc[0]),
            "high": closes + 0.01,
            "low": closes - 0.01,
            "close": closes,
            "volume": [100, 110, 120, 130, 140],
        }
    )


def main() -> None:
    """Run aggregate currency strength and pair ranking examples."""
    pair_data = {
        "EURUSD": make_pair(1.0),
        "GBPUSD": make_pair(1.1),
        "USDJPY": make_pair(150.0),
    }
    request_id = "usage-currency-strength-001"
    strength = calculate_currency_strength(pair_data, period=2, request_id=request_id)
    ranking = get_top_pairs(pair_data, period=2, top_n=2, request_id=request_id)

    print(strength["status"], strength["metadata"])
    print(ranking["status"], ranking["data"])


if __name__ == "__main__":
    main()
