"""Executable usage evidence for volume indicators."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import DataError, MarketDataset, get_market_data
from app.services.indicators import cmf, mfi, obv, price_volume_distribution

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
        _CACHE["dataset"] = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="M5",
            limit=20,
        )
    return _CACHE["dataset"]


def fr_indi_027() -> None:
    """FR-INDI-027: The system shall sum money-flow volume over an inclusive `period` window for one validated `MarketDataset v1`; zero-range bars contribute zero and a complete zero-volume window returns zero."""
    _header(
        "FR-INDI-027: The system shall sum money-flow volume over an inclusive `period` window for one validated `MarketDataset v1`; zero-range bars contribute zero and a complete zero-volume window returns zero."
    )
    result = cmf(_dataset(), period=2)
    print("Result:", result.values["cmf_2"].tolist())


def fr_indi_028() -> None:
    """FR-INDI-028: The system shall start at zero, add volume after a higher close, subtract it after a lower close, and carry forward after an unchanged close."""
    _header(
        "FR-INDI-028: The system shall start at zero, add volume after a higher close, subtract it after a lower close, and carry forward after an unchanged close."
    )
    result = obv(_dataset())
    print("Result:", result.values["obv"].tolist())


def fr_indi_029() -> None:
    """FR-INDI-029: The system shall use typical price × volume over an inclusive `period` flow window; both flows zero returns 50, negative flow zero returns 100, and positive flow zero returns 0."""  # noqa: RUF002 - exact specification text
    _header(
        "FR-INDI-029: The system shall use typical price x volume over an inclusive `period` flow window; both flows zero returns 50, negative flow zero returns 100, and positive flow zero returns 0."
    )
    result = mfi(_dataset(), period=2)
    print("Result:", result.values["mfi_2"].tolist())


def fr_indi_030() -> None:
    """FR-INDI-030: The system shall assign each close to one of `bins` equal-width rolling price bins and return the center of the highest-volume bin; ties resolve to the lowest bin."""
    _header(
        "FR-INDI-030: The system shall assign each close to one of `bins` equal-width rolling price bins and return the center of the highest-volume bin; ties resolve to the lowest bin."
    )
    result = price_volume_distribution(_dataset(), period=2, bins=2)
    print(
        "FR-INDI-030",
        result.values["price_volume_distribution_2_2"].tolist(),
    )


def main() -> None:
    """Run every volume requirement demonstration.

    Returns:
        None.
    """
    try:
        _dataset()
    except DataError as unavailable:
        print(f"Skipping volume examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None
    fr_indi_027()
    fr_indi_028()
    fr_indi_029()
    fr_indi_030()


if __name__ == "__main__":
    main()
