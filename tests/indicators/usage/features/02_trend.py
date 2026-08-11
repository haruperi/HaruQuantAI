"""Executable usage evidence for FEAT-INDI-02 trend indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    adx,
    aroon,
    bollinger_bands,
    ema,
    ema_slope,
    get_indicator_result_values,
    hull_ma,
    linear_regression_trend,
    macd,
    measure_trend_strength,
    project_structural_levels,
    sma,
    supertrend,
    wma,
    zigzag,
)
from tests.indicators.usage._support import (
    get_mt5_usage_dataset,
    print_indicator_evidence,
    print_market_evidence,
    print_requirement_evidence,
    unwrap_indicator_response,
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
        _CACHE["dataset"] = get_mt5_usage_dataset()
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
    print_requirement_evidence("FR-INDI-015", actual_data=values)


def fr_indi_016() -> None:
    """FR-INDI-016: Stage 2 — Calculate SMA through approved trend formula."""
    _header("Stage 2: Trend moving average - SMA formula execution (FR-INDI-016)")
    result = unwrap_indicator_response(sma(_dataset(), period=3))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="SMA calculations")
    print_requirement_evidence("FR-INDI-016", actual_data=values)


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
    print_requirement_evidence("FR-INDI-017", actual_data=values)


def fr_indi_023() -> None:
    """FR-INDI-023: Stage 4 — Calculate weighted moving average trend shape."""
    _header("Stage 4: Trend weighted averaging - WMA formula execution (FR-INDI-023)")
    result = unwrap_indicator_response(wma(_dataset(), period=3))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="WMA calculations")
    print_requirement_evidence("FR-INDI-023", actual_data=values)


def fr_indi_024() -> None:
    """FR-INDI-024: Stage 5 — Calculate Hull MA from nested WMA passes."""
    _header("Stage 5: Trend smoothing - Hull MA formula execution (FR-INDI-024)")
    result = unwrap_indicator_response(hull_ma(_dataset(), period=4))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Hull-MA calculations")
    print_requirement_evidence("FR-INDI-024", actual_data=values)


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
    print_requirement_evidence("FR-INDI-025", actual_data=values)


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
    print_requirement_evidence("FR-INDI-035", actual_data=values)


def fr_indi_050() -> None:
    """FR-INDI-050: Stage 8 — Calculate EMA and ATR-normalized slope (IND-TR-01)."""
    _header("Stage 8: Trend velocity - EMA slope formula execution (FR-INDI-050)")
    result = unwrap_indicator_response(
        ema_slope(_dataset(), period=3, lag=1, atr_period=3)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="EMA-slope calculations")
    print_requirement_evidence("FR-INDI-050", actual_data=values)


def fr_indi_051() -> None:
    """FR-INDI-051: Stage 9 — Calculate OLS linear-regression trend fit (IND-TR-02)."""
    _header(
        "Stage 9: Trend fit contract - linear_regression_trend execution (FR-INDI-051)"
    )
    result = unwrap_indicator_response(linear_regression_trend(_dataset(), period=5))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Linear-regression-trend calculations")
    print_requirement_evidence("FR-INDI-051", actual_data=values)


def fr_indi_052() -> None:
    """FR-INDI-052: Stage 10 — Calculate Aroon Up/Down/Oscillator (IND-TR-04)."""
    _header("Stage 10: Trend extremum age - Aroon formula execution (FR-INDI-052)")
    result = unwrap_indicator_response(aroon(_dataset(), lookback=5))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Aroon calculations")
    print_requirement_evidence("FR-INDI-052", actual_data=values)


def fr_indi_053() -> None:
    """FR-INDI-053: Stage 11 — Calculate MACD line/signal/histogram (IND-TR-05)."""
    _header("Stage 11: Trend convergence - MACD formula execution (FR-INDI-053)")
    result = unwrap_indicator_response(
        macd(_dataset(), fast_period=3, slow_period=6, signal_period=2)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="MACD calculations")
    print_requirement_evidence("FR-INDI-053", actual_data=values)


def fr_indi_054() -> None:
    """FR-INDI-054: Stage 12 — Calculate Supertrend line/direction (IND-TR-06)."""
    _header(
        "Stage 12: Trend band contract - Supertrend formula execution (FR-INDI-054)"
    )
    result = unwrap_indicator_response(
        supertrend(_dataset(), atr_period=3, multiplier=3.0)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Supertrend calculations")
    print_requirement_evidence("FR-INDI-054", actual_data=values)


def main() -> None:
    """Run every trend requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-02 — trend/ — Trend and Moving-Average Calculation\n\n"
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
    fr_indi_050()
    fr_indi_051()
    fr_indi_052()
    fr_indi_053()
    fr_indi_054()
    trend = measure_trend_strength(
        adx_value=30.0,
        positive_directional=25.0,
        negative_directional=10.0,
        fast_average=1.1,
        slow_average=1.0,
        strength_threshold=25.0,
    )
    levels = project_structural_levels(
        [
            {
                "kind": "support",
                "price": float(_dataset().records[-1].low),
                "observed_at": _dataset().records[-1].timestamp,
                "invalidation_price": float(_dataset().records[-1].low),
            }
        ],
        decision_time=_dataset().records[-1].available_at,
    )
    print(f"Trend-strength DATA: {trend.data}")
    print(f"Structural-level DATA: {levels.data}")


if __name__ == "__main__":
    main()
