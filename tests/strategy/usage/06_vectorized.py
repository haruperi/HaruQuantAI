"""Executable real-market input example for vectorized Strategy hosts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import DataError

print("\nREAL INPUT FOR VECTORIZED STRATEGY EVALUATION")
print("=" * 88)
try:
    market = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=300,
        use_cache=False,
    )
except DataError as error:
    print("Live MT5 data unavailable:", error.code)
    sys.exit(3)

print("Source: MT5")
print("Request:", market.request_id)
print("Bars:", market.record_count)
print("Latest completed bar:", market.records[-1].timestamp)
print("Pass this immutable dataset to a registered VectorizedStrategyEvaluator host.")
