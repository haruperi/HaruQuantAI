"""Executable usage evidence for candlestick-pattern indicators."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from typing import Any

from app.services.data import get_market_data
from app.services.indicators import (
    doji,
    engulfing,
    inside_bar,
    pinbar,
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
                limit=20,
            )
        )
    return _CACHE["dataset"]


def fr_indi_031() -> None:
    """FR-INDI-031: The system shall emit `1` when body/range is at most the explicit threshold and `0` otherwise; a zero-range candle is a Doji only when open equals close."""
    _header(
        "FR-INDI-031: The system shall emit `1` when body/range is at most the explicit threshold and `0` otherwise; a zero-range candle is a Doji only when open equals close."
    )
    result = unwrap_indicator_response(doji(_dataset(), threshold=0.1))
    print_indicator_evidence(result, label="Doji calculations")


def fr_indi_032() -> None:
    """FR-INDI-032: The system shall emit `1`, `-1`, or `0`; the first row is warmup and each later result depends only on the current and prior candle bodies."""
    _header(
        "FR-INDI-032: The system shall emit `1`, `-1`, or `0`; the first row is warmup and each later result depends only on the current and prior candle bodies."
    )
    result = unwrap_indicator_response(engulfing(_dataset()))
    print_indicator_evidence(result, label="Engulfing calculations")


def fr_indi_033() -> None:
    """FR-INDI-033: The system shall emit `1`, `-1`, or `0` using fixed non-configurable shadow/body proportions, with bullish precedence for an otherwise ambiguous match."""
    _header(
        "FR-INDI-033: The system shall emit `1`, `-1`, or `0` using fixed non-configurable shadow/body proportions, with bullish precedence for an otherwise ambiguous match."
    )
    result = unwrap_indicator_response(pinbar(_dataset()))
    print_indicator_evidence(result, label="Pinbar calculations")


def fr_indi_034() -> None:
    """FR-INDI-034: The system shall emit `1` only when the current high/low is contained within the prior high/low; the first row is warmup."""
    _header(
        "FR-INDI-034: The system shall emit `1` only when the current high/low is contained within the prior high/low; the first row is warmup."
    )
    result = unwrap_indicator_response(inside_bar(_dataset()))
    print_indicator_evidence(result, label="Inside-bar calculations")


def main() -> None:
    """Run every candlestick-pattern requirement demonstration.

    Returns:
        None.
    """
    try:
        _dataset()
    except RuntimeError as unavailable:
        print(f"Skipping candle examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    print_market_evidence(_dataset())
    fr_indi_031()
    fr_indi_032()
    fr_indi_033()
    fr_indi_034()


if __name__ == "__main__":
    main()
