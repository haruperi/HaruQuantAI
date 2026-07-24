"""Executable usage evidence for volatility indicators."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import DataError, MarketDataset, get_market_data
from app.services.indicators import (
    adr,
    atr,
    rolling_volatility,
    standard_deviation,
)

_CACHE: dict[str, MarketDataset] = {}


def _dataset(timeframe: str) -> MarketDataset:
    """Return one cached real read-only market dataset.

    Args:
        timeframe: Exact requested timeframe.

    Returns:
        A normalized real market dataset.

    Raises:
        DataError: If the configured source is unavailable.
    """
    if timeframe not in _CACHE:
        _CACHE[timeframe] = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe=timeframe,
            limit=20,
        )
    return _CACHE[timeframe]


def fr_indi_018() -> None:
    """FR-INDI-018: The system shall calculate non-negative ATR for one validated `MarketDataset v1` using the approved true-range/smoothing/seed contract, preserve gap and warmup semantics, and return causal metadata without input mutation."""  # noqa: E501 - exact specification text
    result = atr(_dataset("M5"), period=2)
    print("FR-INDI-018", result.values["atr_2"].tolist())


def fr_indi_019() -> None:
    """FR-INDI-019: The system shall calculate ADR for one validated D1 `MarketDataset v1` as the inclusive rolling mean of `high-low`, perform no timeframe aggregation, preserve warmup rows, and return deterministic availability and manifest metadata."""  # noqa: E501 - exact specification text
    result = adr(_dataset("D1"), period=2)
    print("FR-INDI-019", result.values["adr_2"].tolist())


def fr_indi_020() -> None:
    """FR-INDI-020: The system shall calculate rolling volatility for one validated `MarketDataset v1` from `period` log returns using `ddof=1` and annualization 252, return the exact source-qualified output, treat constant prices as zero volatility, and return causal metadata."""  # noqa: E501 - exact specification text
    result = rolling_volatility(_dataset("M5"), period=2)
    print("FR-INDI-020", result.values["rolling_volatility_2"].tolist())


def fr_indi_026() -> None:
    """FR-INDI-026: The system shall calculate rolling sample standard deviation (`ddof=1`) for one validated `MarketDataset v1` over the selected price, return the exact source-qualified output, treat constant prices as zero, and expose causal metadata."""  # noqa: E501 - exact specification text
    result = standard_deviation(_dataset("M5"), period=2)
    print("FR-INDI-026", result.values["standard_deviation_2"].tolist())


def main() -> None:
    """Run every volatility requirement demonstration.

    Returns:
        None.
    """
    try:
        _dataset("M5")
        _dataset("D1")
    except DataError as unavailable:
        print(
            f"Skipping volatility examples: MT5 data unavailable ({unavailable.code})"
        )
        raise SystemExit(3) from None
    fr_indi_018()
    fr_indi_019()
    fr_indi_020()
    fr_indi_026()


if __name__ == "__main__":
    main()
