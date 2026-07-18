"""Explain the real-account prerequisite for RandomWalk triggers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data, to_ohlcv_dataframe
from app.services.data.contracts import DataError

print("\nRANDOMWALK — REAL MT5 EURUSD M5 EVIDENCE CHECK")
print("=" * 88)

try:
    market = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=2,
        use_cache=False,
    )
except DataError as error:
    print("Live MT5 data unavailable:", error.code)
    sys.exit(3)

latest = to_ohlcv_dataframe(market).iloc[-1]
print("Real market data is ready through:", market.end)
print("Latest close:", latest["close"])
print("Trigger evaluation is intentionally blocked.")
print(
    "RandomWalkEvaluator requires real owned-position tags derived from a fresh "
    "Data-owned account snapshot."
)
print("The Data package root does not currently expose that account read.")
print("No empty or fabricated position ownership state was supplied.")
sys.exit(3)
