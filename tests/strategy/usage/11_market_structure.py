"""Explain the real-evidence prerequisite for Market Structure signals."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data, to_ohlcv_dataframe
from app.services.data.contracts import DataError

print("\nMARKET STRUCTURE — REAL MT5 EURUSD M5 EVIDENCE CHECK")
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

latest = to_ohlcv_dataframe(market).iloc[-1]
print("Real market data is ready through:", market.end)
print("Latest close:", latest["close"])
print("Signal evaluation is intentionally blocked.")
print(
    "MarketStructureEvaluator requires exactly eight externally supplied, "
    "provenance-bound ZigZag extremes."
)
print("No current Data or Indicators package-root export supplies that evidence.")
print("No substitute pivots or synthetic ZigZag values were invented.")
sys.exit(3)
