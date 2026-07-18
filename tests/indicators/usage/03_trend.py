"""Executable indicators trend feature examples."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import (
    DataError,
    MarketDataset,
)
from app.services.indicators.trend import (
    adx,
    bollinger_bands,
    ema,
    hull_ma,
    sma,
    wma,
)

_CACHE: dict[str, MarketDataset] = {}


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


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
    print(f"Skipping trend examples: MT5 data unavailable ({error.code})")
    sys.exit(3)

_header("Example 1: Calculate EMA over a normalized dataset")
result_ema = ema(data, period=3)
print(f"EMA columns: {list(result_ema.values.columns)}")
print("EMA Full Table Values: ")
print(f"{result_ema.values}")

_header("Example 2: Calculate SMA over a normalized dataset")
result_sma = sma(data, period=3)
print(f"SMA columns: {list(result_sma.values.columns)}")
print("View the specific indicator column 'sma_3': ")
print(f"{result_sma.values['sma_3']}")

_header("Example 3: Calculate WMA over a normalized dataset")
result_wma = wma(data, period=3)
print("View the indicator columns joined with the original market data (OHLCV): ")
print(f"{result_wma.join_to(data)}")

_header("Example 4: Calculate Hull MA over a normalized dataset")
result_hma = hull_ma(data, period=3)
print("View the copy-safe values-only projection: ")
print(f"{result_hma.values_only}")

_header("Example 5: Calculate Bollinger Bands over a normalized dataset")
result_bb = bollinger_bands(data, period=3, std_dev=2.0)
print(f"Bollinger Bands columns: {list(result_bb.output_columns)}")

_header("Example 6: Calculate ADX, +DI, and -DI over a normalized dataset")
result_adx = adx(data, period=2)
print(f"ADX columns: {list(result_adx.values.columns)}")
print(f"ADX values: {result_adx.values['adx_2'].tolist()}")
print(f"Plus DI values: {result_adx.values['plus_di_2'].tolist()}")
print(f"Minus DI values: {result_adx.values['minus_di_2'].tolist()}")
