"""Executable usage evidence for trend indicators."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from typing import Any

from app.services.data import get_market_data
from app.services.indicators import (
    adx,
    bollinger_bands,
    ema,
    hull_ma,
    sma,
    wma,
    zigzag,
)

from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
    unwrap_market_data_response,
)

MarketDataset = Any
_CACHE: dict[str, MarketDataset] = {}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _dataset() -> MarketDataset:
    """Return one cached real read-only market dataset.

    Returns:
        A normalized real market dataset.

    Raises:
        RuntimeError: If the configured source is unavailable.
    """
    if "dataset" not in _CACHE:
        _CACHE["dataset"] = unwrap_market_data_response(
            get_market_data(
                source_id="mt5",
                symbol="EURUSD",
                timeframe="M5",
                limit=30,
            )
        )
    return _CACHE["dataset"]


def fr_indi_015() -> None:
    """FR-INDI-015: The system shall calculate EMA for one validated `MarketDataset v1` using the approved seed/smoothing contract, return `ema_{period}` or the exact source-qualified name, preserve warmup rows, and expose causal availability and a deterministic manifest without mutating input."""
    _header(
        "FR-INDI-015: The system shall calculate EMA for one validated `MarketDataset v1` using the approved seed/smoothing contract, return `ema_{period}` or the exact source-qualified name, preserve warmup rows, and expose causal availability and a deterministic manifest without mutating input."
    )
    result = unwrap_indicator_response(ema(_dataset(), period=3))
    print_indicator_evidence(result, label="EMA calculations")


def fr_indi_016() -> None:
    """FR-INDI-016: The system shall calculate SMA for one validated `MarketDataset v1` over the approved inclusive window, return the exact deterministic source-qualified output, preserve warmup rows, and expose causal availability and a deterministic manifest without mutating input."""
    _header(
        "FR-INDI-016: The system shall calculate SMA for one validated `MarketDataset v1` over the approved inclusive window, return the exact deterministic source-qualified output, preserve warmup rows, and expose causal availability and a deterministic manifest without mutating input."
    )
    result = unwrap_indicator_response(sma(_dataset(), period=3))
    print_indicator_evidence(result, label="SMA calculations")


def fr_indi_017() -> None:
    """FR-INDI-017: The system shall calculate approved ADX, +DI, and -DI values for one validated `MarketDataset v1`, return the three canonical columns with warmup/availability metadata, and handle zero range deterministically."""
    _header(
        "FR-INDI-017: The system shall calculate approved ADX, +DI, and -DI values for one validated `MarketDataset v1`, return the three canonical columns with warmup/availability metadata, and handle zero range deterministically."
    )
    result = unwrap_indicator_response(adx(_dataset(), period=2))
    print_indicator_evidence(result, label="ADX/+DI/-DI calculations")


def fr_indi_023() -> None:
    """FR-INDI-023: The system shall calculate WMA for one validated `MarketDataset v1` using linear weights `1..period` over the inclusive window, return the exact source-qualified output, preserve warmup rows, and expose causal metadata."""
    _header(
        "FR-INDI-023: The system shall calculate WMA for one validated `MarketDataset v1` using linear weights `1..period` over the inclusive window, return the exact source-qualified output, preserve warmup rows, and expose causal metadata."
    )
    result = unwrap_indicator_response(wma(_dataset(), period=3))
    print_indicator_evidence(result, label="WMA calculations")


def fr_indi_024() -> None:
    """FR-INDI-024: The system shall calculate Hull MA for one validated `MarketDataset v1` from two nested half/full-period WMA passes and one floor-sqrt-period-length WMA pass, return the exact source-qualified output, preserve warmup rows, and expose causal metadata."""
    _header(
        "FR-INDI-024: The system shall calculate Hull MA for one validated `MarketDataset v1` from two nested half/full-period WMA passes and one floor-sqrt-period-length WMA pass, return the exact source-qualified output, preserve warmup rows, and expose causal metadata."
    )
    result = unwrap_indicator_response(hull_ma(_dataset(), period=4))
    print_indicator_evidence(result, label="Hull-MA calculations")


def fr_indi_025() -> None:
    """FR-INDI-025: The system shall calculate Bollinger Bands for one validated `MarketDataset v1` as an SMA basis with symmetric standard-deviation bands, return the three canonical columns sharing one warmup mask, and expose causal metadata."""
    _header(
        "FR-INDI-025: The system shall calculate Bollinger Bands for one validated `MarketDataset v1` as an SMA basis with symmetric standard-deviation bands, return the three canonical columns sharing one warmup mask, and expose causal metadata."
    )
    result = unwrap_indicator_response(
        bollinger_bands(_dataset(), period=3, std_dev=2.0)
    )
    print_indicator_evidence(result, label="Bollinger-band calculations")


def fr_indi_035() -> None:
    """FR-INDI-035: The system shall identify unique alternating high/low extrema over an explicit symmetric `depth` window and publish each value and type only on its causal confirmation row; tied extrema and consecutive candidates of the same type are not pivots, and a published pivot is never revised."""
    _header(
        "FR-INDI-035: The system shall identify unique alternating high/low extrema over an explicit symmetric `depth` window and publish each value and type only on its causal confirmation row; tied extrema and consecutive candidates of the same type are not pivots, and a published pivot is never revised."
    )
    result = unwrap_indicator_response(zigzag(_dataset(), depth=2))
    print_indicator_evidence(result, label="Causally confirmed Zigzag rows")


def main() -> None:
    """Run every trend requirement demonstration.

    Returns:
        None.
    """
    try:
        _dataset()
    except RuntimeError as unavailable:
        print(f"Skipping trend examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    print_market_evidence(_dataset())
    fr_indi_015()
    fr_indi_016()
    fr_indi_017()
    fr_indi_023()
    fr_indi_024()
    fr_indi_025()
    fr_indi_035()


if __name__ == "__main__":
    main()
