"""Executable usage evidence for trend indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_market_data
from app.services.indicators import (
    adx,
    bollinger_bands,
    ema,
    get_indicator_result_values,
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
                limit=30,
            )
        )
    return _CACHE["dataset"]


def fr_indi_015() -> None:
    """FR-INDI-015: Stage 1 — Calculate EMA through approved trend formula."""
    _header(
        "Stage 1: Trend trendline construction - EMA formula execution (FR-INDI-015)"
    )
    result = unwrap_indicator_response(ema(_dataset(), period=3))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="EMA calculations")


def fr_indi_016() -> None:
    """FR-INDI-016: Stage 2 — Calculate SMA through approved trend formula."""
    _header("Stage 2: Trend moving average - SMA formula execution (FR-INDI-016)")
    result = unwrap_indicator_response(sma(_dataset(), period=3))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="SMA calculations")


def fr_indi_017() -> None:
    """FR-INDI-017: Stage 3 — Calculate directional trend strength indicators."""
    _header(
        "Stage 3: Trend directional strength - ADX/DI formula execution (FR-INDI-017)"
    )
    result = unwrap_indicator_response(adx(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="ADX/+DI/-DI calculations")


def fr_indi_023() -> None:
    """FR-INDI-023: Stage 4 — Calculate weighted moving average trend shape."""
    _header("Stage 4: Trend weighted averaging - WMA formula execution (FR-INDI-023)")
    result = unwrap_indicator_response(wma(_dataset(), period=3))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="WMA calculations")


def fr_indi_024() -> None:
    """FR-INDI-024: Stage 5 — Calculate Hull MA from nested WMA passes."""
    _header("Stage 5: Trend smoothing - Hull MA formula execution (FR-INDI-024)")
    result = unwrap_indicator_response(hull_ma(_dataset(), period=4))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Hull-MA calculations")


def fr_indi_025() -> None:
    """FR-INDI-025: Stage 6 — Calculate Bollinger Bands trend envelope."""
    _header(
        "Stage 6: Trend envelope contract - Bollinger Bands formula execution (FR-INDI-025)"
    )
    result = unwrap_indicator_response(
        bollinger_bands(_dataset(), period=3, std_dev=2.0)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Bollinger-band calculations")


def fr_indi_035() -> None:
    """FR-INDI-035: Stage 7 — Compute causal trend pivot extrema."""
    _header(
        "Stage 7: Trend extremum extraction - Zigzag confirmation execution (FR-INDI-035)"
    )
    result = unwrap_indicator_response(zigzag(_dataset(), depth=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Causally confirmed Zigzag rows")


def main() -> None:
    """Run every trend requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-03 — trend/ — Trend and Moving-Average Calculation\n\n"
        "Purpose: Compute the approved trend indicators through stateless vectorized batch functions.\n\n"
        "Module flow:\n"
        "-> normalized values + config\n"
        "-> Core validation\n"
        "-> approved trend formula\n"
        "-> IndicatorResult"
    )

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
