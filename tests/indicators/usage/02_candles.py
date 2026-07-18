"""Executable indicators candlestick patterns examples."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import DataError, MarketDataset
from app.services.indicators.candles import doji, engulfing, inside_bar, pinbar


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
    print(f"Skipping candle examples: MT5 data unavailable ({error.code})")
    sys.exit(3)

_header("Example 1: Identify Doji candlesticks")
result_doji = doji(data, threshold=0.1)
print(f"Doji values: {result_doji.values['doji'].tolist()}")
print(f"Output columns: {result_doji.output_columns}")

_header("Example 2: Identify Engulfing candlesticks")
result_engulfing = engulfing(data)
print(f"Engulfing values: {result_engulfing.values['engulfing'].tolist()}")
print(f"Output columns: {result_engulfing.output_columns}")

_header("Example 3: Identify Pinbar candlesticks")
result_pinbar = pinbar(data)
print(f"Pinbar values: {result_pinbar.values['pinbar'].tolist()}")
print(f"Output columns: {result_pinbar.output_columns}")

_header("Example 4: Identify Inside Bar candlesticks")
result_inside = inside_bar(data)
print(f"Inside Bar values: {result_inside.values['inside_bar'].tolist()}")
print(f"Output columns: {result_inside.output_columns}")
