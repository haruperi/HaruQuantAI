"""Executable indicators volume feature examples."""

import sys
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data
from app.services.data.contracts import DataError, MarketDataset
from app.services.indicators.volume import (
    cmf,
    mfi,
    obv,
    price_volume_distribution,
)


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


def main() -> None:
    """Run the volume-indicator feature usage examples.

    Demonstrates ``FR-INDI-027`` through ``FR-INDI-030`` end-to-end against
    real market data using only documented public exports. Exits with status
    ``3`` when the live market-data source is unavailable, which the
    integration runner treats as a skip rather than a failure.
    """
    try:
        data = _get_dataset()
    except DataError as unavailable:
        print(f"Skipping volume examples: MT5 data unavailable ({unavailable.code})")
        sys.exit(3)

    _header("Example 1: Calculate Chaikin Money Flow")
    result_cmf = cmf(data, period=2)
    print(f"CMF values: {result_cmf.values['cmf_2'].tolist()}")
    print(f"Output columns: {result_cmf.output_columns}")

    _header("Example 2: Calculate On-Balance Volume")
    result_obv = obv(data)
    print(f"OBV values: {result_obv.values['obv'].tolist()}")
    print(f"Output columns: {result_obv.output_columns}")

    _header("Example 3: Calculate Money Flow Index")
    result_mfi = mfi(data, period=2)
    print(f"MFI values: {result_mfi.values['mfi_2'].tolist()}")
    print(f"Output columns: {result_mfi.output_columns}")

    _header("Example 4: Calculate rolling volume-by-price POC")
    result_dist = price_volume_distribution(data, period=2, bins=2)
    dist_values = result_dist.values["price_volume_distribution_2_2"].tolist()
    print(f"Price-volume distribution values: {dist_values}")
    print(f"Output columns: {result_dist.output_columns}")


if __name__ == "__main__":
    main()
