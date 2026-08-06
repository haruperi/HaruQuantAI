"""Executable usage evidence for candlestick-pattern indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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
    print_requirement_evidence,
    unwrap_indicator_response,
    unwrap_market_data_response,
)


def _feature_header(title: str) -> None:
    """Print feature header and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
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


MarketDataset = Any
_CACHE: dict[str, MarketDataset] = {}


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
    """FR-INDI-031: Stage 1 — Detect doji using body-to-range rule."""
    _header(
        "Stage 1: Pattern Body-Ratio Rules - Doji Body/Range Classification (FR-INDI-031)"
    )
    result = unwrap_indicator_response(doji(_dataset(), threshold=0.1))
    print(_format_result(result))
    print(
        f"Data -> rows={len(result.values)}, pattern_columns={list(result.values.columns)}"
    )
    print_indicator_evidence(result, label="Doji calculations")
    print_requirement_evidence("FR-INDI-031", actual_data=result.values)


def fr_indi_032() -> None:
    """FR-INDI-032: Stage 2 — Detect engulfing from two-bar body dependency."""
    _header("Stage 2: Pattern Dependencies - Two-Bar Engulfing Contract (FR-INDI-032)")
    result = unwrap_indicator_response(engulfing(_dataset()))
    print(_format_result(result))
    print(f"Data -> rows={len(result.values)}, columns={list(result.values.columns)}")
    print_indicator_evidence(result, label="Engulfing calculations")
    print_requirement_evidence("FR-INDI-032", actual_data=result.values)


def fr_indi_033() -> None:
    """FR-INDI-033: Stage 3 — Detect pinbar with fixed body-shape precedence."""
    _header("Stage 3: Pattern Geometry - Pinbar Classification Contract (FR-INDI-033)")
    result = unwrap_indicator_response(pinbar(_dataset()))
    print(_format_result(result))
    print(f"Data -> rows={len(result.values)}, columns={list(result.values.columns)}")
    print_indicator_evidence(result, label="Pinbar calculations")
    print_requirement_evidence("FR-INDI-033", actual_data=result.values)


def fr_indi_034() -> None:
    """FR-INDI-034: Stage 4 — Detect containment using prior high-low envelope."""
    _header("Stage 4: Pattern Containment - Inside-Bar Detection Rule (FR-INDI-034)")
    result = unwrap_indicator_response(inside_bar(_dataset()))
    print(_format_result(result))
    print(f"Data -> rows={len(result.values)}, columns={list(result.values.columns)}")
    print_indicator_evidence(result, label="Inside-bar calculations")
    print_requirement_evidence("FR-INDI-034", actual_data=result.values)


def main() -> None:
    """Run all feature requirements in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-INDI-02 — candles/ — Candlestick Pattern Labelling\n\n"
        "Purpose: Emit deterministic single- and two-bar pattern labels without retrospective confirmation or repainting.\n\n"
        "Module flow:\n"
        "-> normalized OHLCV bars + config\n"
        "-> validation.py\n"
        "-> approved pattern formula\n"
        "-> IndicatorResult"
    )

    # Stage 1: body/range inputs map directly to doji output.
    # Stage 2: canonical two-bar dependency for engulfing.
    # Stage 3: fixed-geometry pinbar rule and bullish precedence.
    # Stage 4: containment semantics for inside-bar labels.
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
