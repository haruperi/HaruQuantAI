"""Executable indicators momentum feature examples."""

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
from app.services.indicators.momentum import rsi, williams_r

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


def _get_dataset() -> MarketDataset:
    """Retrieve real market dataset.

    Returns:
        A MarketDataset instance.
    """
    if "dataset" in _CACHE:
        return _CACHE["dataset"]
    dataset = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M5",
        limit=20,
    )
    print("Using real MT5 EURUSD market data.")
    _CACHE["dataset"] = dataset
    return dataset


try:
    data = _get_dataset()
except DataError as error:
    print(f"Skipping momentum examples: MT5 data unavailable ({error.code})")
    sys.exit(3)

_header("Example 1: Calculate RSI over a normalized dataset")
result_rsi = rsi(data, period=2)
print(f"RSI columns: {list(result_rsi.values.columns)}")
print(f"RSI values: {result_rsi.values['rsi_2'].tolist()}")

_header("Example 2: Calculate Williams %R over a normalized dataset")
result_williams = williams_r(data, period=2)
print(f"Williams %R columns: {list(result_williams.values.columns)}")
print(f"Williams %R values: {result_williams.values['williams_r_2'].tolist()}")
