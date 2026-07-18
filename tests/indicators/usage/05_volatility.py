"""Executable indicators volatility feature examples."""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import (
    DataError,
    MarketDataset,
)
from app.services.indicators.volatility import (
    adr,
    atr,
    rolling_volatility,
    standard_deviation,
)

_START = datetime(2026, 1, 1, tzinfo=UTC)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


_CACHE: dict[str, MarketDataset] = {}


def _get_intraday_dataset() -> MarketDataset:
    """Retrieve real market intraday dataset.

    Returns:
        A MarketDataset instance.
    """
    if "intraday" in _CACHE:
        return _CACHE["intraday"]
    dataset = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=20,
    )
    print("Using real MT5 EURUSD M5 market data.")
    _CACHE["intraday"] = dataset
    return dataset


def _get_daily_dataset() -> MarketDataset:
    """Retrieve real market daily dataset.

    Returns:
        A MarketDataset instance.
    """
    if "daily" in _CACHE:
        return _CACHE["daily"]
    dataset = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="D1",
        limit=10,
    )
    print("Using real MT5 EURUSD D1 market data.")
    _CACHE["daily"] = dataset
    return dataset


try:
    intraday_data = _get_intraday_dataset()
    daily_data = _get_daily_dataset()
except DataError as error:
    print(f"Skipping volatility examples: MT5 data unavailable ({error.code})")
    sys.exit(3)

_header("Example 1: Calculate ATR over a normalized intraday dataset")
result_atr = atr(intraday_data, period=2)
print(f"ATR columns: {list(result_atr.values.columns)}")
print(f"ATR values: {result_atr.values['atr_2'].tolist()}")

_header("Example 2: Calculate ADR over a normalized D1 dataset")
result_adr = adr(daily_data, period=2)
print(f"ADR columns: {list(result_adr.values.columns)}")
print(f"ADR values: {result_adr.values['adr_2'].tolist()}")

_header("Example 3: Calculate rolling volatility over a normalized dataset")
result_vol = rolling_volatility(intraday_data, period=2)
print(f"Rolling volatility columns: {list(result_vol.values.columns)}")
print(
    f"Rolling volatility values: {result_vol.values['rolling_volatility_2'].tolist()}"
)

_header("Example 4: Calculate rolling price standard deviation")
result_std = standard_deviation(intraday_data, period=2)
print(
    f"Standard deviation values: {result_std.values['standard_deviation_2'].tolist()}"
)
