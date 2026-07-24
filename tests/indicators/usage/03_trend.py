"""Executable usage evidence for trend indicators."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import DataError, MarketDataset, get_market_data
from app.services.indicators import adx, bollinger_bands, ema, hull_ma, sma, wma, zigzag

_CACHE: dict[str, MarketDataset] = {}


def _dataset() -> MarketDataset:
    """Return one cached real read-only market dataset.

    Returns:
        A normalized real market dataset.

    Raises:
        DataError: If the configured source is unavailable.
    """
    if "dataset" not in _CACHE:
        _CACHE["dataset"] = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="M5",
            limit=30,
        )
    return _CACHE["dataset"]


def fr_indi_015() -> None:
    """FR-INDI-015: The system shall calculate EMA for one validated `MarketDataset v1` using the approved seed/smoothing contract, return `ema_{period}` or the exact source-qualified name, preserve warmup rows, and expose causal availability and a deterministic manifest without mutating input."""  # noqa: E501 - exact specification text
    result = ema(_dataset(), period=3)
    print("FR-INDI-015", result.values["ema_3"].tolist())


def fr_indi_016() -> None:
    """FR-INDI-016: The system shall calculate SMA for one validated `MarketDataset v1` over the approved inclusive window, return the exact deterministic source-qualified output, preserve warmup rows, and expose causal availability and a deterministic manifest without mutating input."""  # noqa: E501 - exact specification text
    result = sma(_dataset(), period=3)
    print("FR-INDI-016", result.values["sma_3"].tolist())


def fr_indi_017() -> None:
    """FR-INDI-017: The system shall calculate approved ADX, +DI, and -DI values for one validated `MarketDataset v1`, return the three canonical columns with warmup/availability metadata, and handle zero range deterministically."""  # noqa: E501 - exact specification text
    result = adx(_dataset(), period=2)
    print("FR-INDI-017", list(result.output_columns))


def fr_indi_023() -> None:
    """FR-INDI-023: The system shall calculate WMA for one validated `MarketDataset v1` using linear weights `1..period` over the inclusive window, return the exact source-qualified output, preserve warmup rows, and expose causal metadata."""  # noqa: E501 - exact specification text
    result = wma(_dataset(), period=3)
    print("FR-INDI-023", result.values["wma_3"].tolist())


def fr_indi_024() -> None:
    """FR-INDI-024: The system shall calculate Hull MA for one validated `MarketDataset v1` from two nested half/full-period WMA passes and one `⌊√period⌋`-length WMA pass, return the exact source-qualified output, preserve warmup rows, and expose causal metadata."""  # noqa: E501 - exact specification text
    result = hull_ma(_dataset(), period=4)
    print("FR-INDI-024", result.values["hull_ma_4"].tolist())


def fr_indi_025() -> None:
    """FR-INDI-025: The system shall calculate Bollinger Bands for one validated `MarketDataset v1` as an SMA basis with symmetric standard-deviation bands, return the three canonical columns sharing one warmup mask, and expose causal metadata."""  # noqa: E501 - exact specification text
    result = bollinger_bands(_dataset(), period=3, std_dev=2.0)
    print("FR-INDI-025", list(result.output_columns))


def fr_indi_035() -> None:
    """FR-INDI-035: The system shall identify unique alternating high/low extrema over an explicit symmetric `depth` window and publish each value and type only on its causal confirmation row; tied extrema and consecutive candidates of the same type are not pivots, and a published pivot is never revised."""  # noqa: E501
    result = zigzag(_dataset(), depth=2)
    print("FR-INDI-035", result.values["zigzag_value_2"].dropna().tolist())


def main() -> None:
    """Run every trend requirement demonstration.

    Returns:
        None.
    """
    try:
        _dataset()
    except DataError as unavailable:
        print(f"Skipping trend examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    fr_indi_015()
    fr_indi_016()
    fr_indi_017()
    fr_indi_023()
    fr_indi_024()
    fr_indi_025()
    fr_indi_035()


if __name__ == "__main__":
    main()
