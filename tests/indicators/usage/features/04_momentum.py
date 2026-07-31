"""Executable usage evidence for momentum indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_market_data
from app.services.indicators import (
    get_indicator_result_values,
    rsi,
    williams_r,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    unwrap_indicator_response,
    unwrap_market_data_response,
)

MarketDataset = Any
_CACHE: dict[str, MarketDataset] = {}


def _feature_header(title: str) -> None:
    """Print the feature banner and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one section heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _dataset() -> MarketDataset:
    """Return one cached real read-only market dataset."""

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
    """FR-INDI-021: Stage 1 — Calculate RSI through approved oscillator formula."""
    _header("Stage 1: Momentum bound contract - RSI formula execution (FR-INDI-021)")
    result = unwrap_indicator_response(rsi(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="RSI calculations")


def fr_indi_022() -> None:
    """FR-INDI-022: Stage 2 — Calculate Williams %R bounded momentum oscillator."""
    _header(
        "Stage 2: Oscillator range contract - Williams %R formula execution (FR-INDI-022)"
    )
    result = unwrap_indicator_response(williams_r(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Williams %R calculations")


def main() -> None:
    """Run every momentum requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-04 — momentum/ — Momentum Oscillator Calculation\n\n"
        "Purpose: Compute the approved bounded momentum oscillators.\n\n"
        "Module flow:\n"
        "-> normalized OHLC/source values\n"
        "-> Core validation\n"
        "-> approved oscillator formula\n"
        "-> IndicatorResult"
    )

    try:
        _dataset()
    except RuntimeError as unavailable:
        print(f"Skipping momentum examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None

    print_market_evidence(_dataset())
    fr_indi_021()
    fr_indi_022()


if __name__ == "__main__":
    main()
