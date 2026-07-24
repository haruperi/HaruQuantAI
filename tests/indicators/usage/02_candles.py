"""Executable usage evidence for candlestick-pattern indicators."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import DataError, MarketDataset, get_market_data
from app.services.indicators import doji, engulfing, inside_bar, pinbar

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
            limit=20,
        )
    return _CACHE["dataset"]


def fr_indi_031() -> None:
    """FR-INDI-031: The system shall emit `1` when body/range is at most the explicit threshold and `0` otherwise; a zero-range candle is a Doji only when open equals close."""  # noqa: E501 - exact specification text
    result = doji(_dataset(), threshold=0.1)
    print("FR-INDI-031", result.values["doji"].tolist())


def fr_indi_032() -> None:
    """FR-INDI-032: The system shall emit `1`, `-1`, or `0`; the first row is warmup and each later result depends only on the current and prior candle bodies."""  # noqa: E501 - exact specification text
    result = engulfing(_dataset())
    print("FR-INDI-032", result.values["engulfing"].tolist())


def fr_indi_033() -> None:
    """FR-INDI-033: The system shall emit `1`, `-1`, or `0` using fixed non-configurable shadow/body proportions, with bullish precedence for an otherwise ambiguous match."""  # noqa: E501 - exact specification text
    result = pinbar(_dataset())
    print("FR-INDI-033", result.values["pinbar"].tolist())


def fr_indi_034() -> None:
    """FR-INDI-034: The system shall emit `1` only when the current high/low is contained within the prior high/low; the first row is warmup."""  # noqa: E501 - exact specification text
    result = inside_bar(_dataset())
    print("FR-INDI-034", result.values["inside_bar"].tolist())


def main() -> None:
    """Run every candlestick-pattern requirement demonstration.

    Returns:
        None.
    """
    try:
        _dataset()
    except DataError as unavailable:
        print(f"Skipping candle examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    fr_indi_031()
    fr_indi_032()
    fr_indi_033()
    fr_indi_034()


if __name__ == "__main__":
    main()
