"""Executable usage evidence for momentum indicators."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import DataError, MarketDataset, get_market_data
from app.services.indicators import rsi, williams_r

from tests.indicators.usage._support import (
    unwrap_indicator_response,
    unwrap_market_data_response,
)

_CACHE: dict[str, MarketDataset] = {}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _dataset() -> MarketDataset:
    """Return one cached real read-only market dataset.

    Returns:
        A normalized real market dataset.

    Raises:
        DataError: If the configured source is unavailable.
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


def fr_indi_021() -> None:
    """FR-INDI-021: The system shall calculate RSI for one validated `MarketDataset v1` using the approved gain/loss smoothing and seed contract, return the exact source-qualified output, keep values within approved bounds, handle flat/zero-gain/zero-loss windows deterministically, and expose causal metadata."""
    _header(
        "FR-INDI-021: The system shall calculate RSI for one validated `MarketDataset v1` using the approved gain/loss smoothing and seed contract, return the exact source-qualified output, keep values within approved bounds, handle flat/zero-gain/zero-loss windows deterministically, and expose causal metadata."
    )
    result = unwrap_indicator_response(rsi(_dataset(), period=2))
    print("Result:", result.values["rsi_2"].tolist())


def fr_indi_022() -> None:
    """FR-INDI-022: The system shall calculate Williams %R for one validated `MarketDataset v1` over the approved inclusive high/low window, enforce approved bounds and zero-range behavior, preserve warmup rows, and expose causal metadata."""
    _header(
        "FR-INDI-022: The system shall calculate Williams %R for one validated `MarketDataset v1` over the approved inclusive high/low window, enforce approved bounds and zero-range behavior, preserve warmup rows, and expose causal metadata."
    )
    result = unwrap_indicator_response(williams_r(_dataset(), period=2))
    print("Result:", result.values["williams_r_2"].tolist())


def main() -> None:
    """Run every momentum requirement demonstration.

    Returns:
        None.
    """
    try:
        _dataset()
    except DataError as unavailable:
        print(f"Skipping momentum examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    fr_indi_021()
    fr_indi_022()


if __name__ == "__main__":
    main()
