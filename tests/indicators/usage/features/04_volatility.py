"""Executable usage evidence for FEAT-INDI-04 volatility indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    adr,
    atr,
    atr_percent,
    bollinger_bandwidth,
    ewma_volatility,
    garman_klass_volatility,
    get_indicator_result_values,
    measure_market_speed,
    measure_volatility_envelope,
    parkinson_volatility,
    project_market_overlay,
    rogers_satchell_volatility,
    rolling_volatility,
    standard_deviation,
    volatility_of_volatility,
    volatility_percentile,
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
    """Print one example heading."""
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


def fr_indi_018() -> None:
    """FR-INDI-018: Stage 1 — Calculate ATR from approved range contract."""
    _header("Stage 1: Volatility range contract - ATR formula execution (FR-INDI-018)")
    result = unwrap_indicator_response(atr(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="ATR calculations")
    print_requirement_evidence("FR-INDI-018", actual_data=values)


def fr_indi_019() -> None:
    """FR-INDI-019: Stage 2 — Calculate ADR on deterministic D1 ranges."""
    _header("Stage 2: Range mean contract - ADR formula execution (FR-INDI-019)")
    result = unwrap_indicator_response(
        adr(get_mt5_usage_dataset(timeframe="D1"), period=2)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="ADR calculations")
    print_requirement_evidence("FR-INDI-019", actual_data=values)


def fr_indi_020() -> None:
    """FR-INDI-020: Stage 3 — Calculate rolling volatility from returns."""
    _header(
        "Stage 3: Return-volatility contract - rolling_volatility execution (FR-INDI-020)"
    )
    result = unwrap_indicator_response(rolling_volatility(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Rolling-volatility calculations")
    print_requirement_evidence("FR-INDI-020", actual_data=values)


def fr_indi_026() -> None:
    """FR-INDI-026: Stage 4 — Calculate sample standard deviation on selected source."""
    _header(
        "Stage 4: Price-volatility contract - standard_deviation execution (FR-INDI-026)"
    )
    result = unwrap_indicator_response(standard_deviation(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Standard-deviation calculations")
    print_requirement_evidence("FR-INDI-026", actual_data=values)


def fr_indi_042() -> None:
    """FR-INDI-042: Stage 5 — Calculate ATR% (IND-VOL-02) from close-normalized ATR."""
    _header("Stage 5: Normalized-ATR contract - atr_percent execution (FR-INDI-042)")
    result = unwrap_indicator_response(atr_percent(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="ATR% calculations")
    print_requirement_evidence("FR-INDI-042", actual_data=values)


def fr_indi_043() -> None:
    """FR-INDI-043: Stage 6 — Calculate EWMA volatility (IND-VOL-04)."""
    _header(
        "Stage 6: RiskMetrics-EWMA contract - ewma_volatility execution (FR-INDI-043)"
    )
    result = unwrap_indicator_response(ewma_volatility(_dataset(), decay=0.94))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="EWMA-volatility calculations")
    print_requirement_evidence("FR-INDI-043", actual_data=values)


def fr_indi_044() -> None:
    """FR-INDI-044: Stage 7 — Calculate Parkinson range volatility (IND-VOL-05)."""
    _header(
        "Stage 7: Parkinson-range contract - parkinson_volatility execution (FR-INDI-044)"
    )
    result = unwrap_indicator_response(parkinson_volatility(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Parkinson-volatility calculations")
    print_requirement_evidence("FR-INDI-044", actual_data=values)


def fr_indi_045() -> None:
    """FR-INDI-045: Stage 8 — Calculate Garman-Klass volatility (IND-VOL-06)."""
    _header(
        "Stage 8: Garman-Klass contract - garman_klass_volatility execution (FR-INDI-045)"
    )
    result = unwrap_indicator_response(garman_klass_volatility(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Garman-Klass-volatility calculations")
    print_requirement_evidence("FR-INDI-045", actual_data=values)


def fr_indi_046() -> None:
    """FR-INDI-046: Stage 9 — Calculate Rogers-Satchell volatility (IND-VOL-07)."""
    _header(
        "Stage 9: Rogers-Satchell contract - rogers_satchell_volatility execution "
        "(FR-INDI-046)"
    )
    result = unwrap_indicator_response(rogers_satchell_volatility(_dataset(), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Rogers-Satchell-volatility calculations")
    print_requirement_evidence("FR-INDI-046", actual_data=values)


def fr_indi_047() -> None:
    """FR-INDI-047: Stage 10 — Calculate Bollinger BandWidth (IND-VOL-08)."""
    _header(
        "Stage 10: BandWidth contract - bollinger_bandwidth execution (FR-INDI-047)"
    )
    result = unwrap_indicator_response(
        bollinger_bandwidth(_dataset(), period=2, std_dev=2.0)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Bollinger-BandWidth calculations")
    print_requirement_evidence("FR-INDI-047", actual_data=values)


def fr_indi_048() -> None:
    """FR-INDI-048: Stage 11 — Calculate volatility percentile/z-score (IND-VOL-09)."""
    _header(
        "Stage 11: Percentile/z-score contract - volatility_percentile execution "
        "(FR-INDI-048)"
    )
    result = unwrap_indicator_response(
        volatility_percentile(_dataset(), reference_period=3, vol_period=2)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Volatility-percentile calculations")
    print_requirement_evidence("FR-INDI-048", actual_data=values)


def fr_indi_049() -> None:
    """FR-INDI-049: Stage 12 — Calculate volatility of volatility (IND-VOL-10)."""
    _header("Stage 12: VoV contract - volatility_of_volatility execution (FR-INDI-049)")
    result = unwrap_indicator_response(
        volatility_of_volatility(_dataset(), period=2, vol_period=2)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Volatility-of-volatility calculations")
    print_requirement_evidence("FR-INDI-049", actual_data=values)


def fr_indi_085() -> None:
    """FR-INDI-085: Project prior-settled volatility and market overlays."""
    dataset = _dataset()
    latest = dataset.records[-1]
    projection = project_market_overlay(
        dataset,
        pip_size=0.0001,
        last_price=float(latest.close),
    )
    print_requirement_evidence("FR-INDI-085", actual_data=projection)


def main() -> None:
    """Run every volatility requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-04 — volatility/ — Volatility and Range Calculation\n\n"
        "Purpose: Compute approved range- and return-based volatility measures.\n\n"
        "Module flow:\n"
        "-> normalized OHLC/source values\n"
        "-> Core validation\n"
        "-> approved volatility formula\n"
        "-> IndicatorResult"
    )

    try:
        _dataset()
        _dataset()
    except RuntimeError as unavailable:
        print(
            f"Skipping volatility examples: MT5 data unavailable ({unavailable.code})"
        )
        raise SystemExit(3) from None

    print_market_evidence(_dataset())
    print_market_evidence(_dataset())
    fr_indi_018()
    fr_indi_019()
    fr_indi_020()
    fr_indi_026()
    fr_indi_042()
    fr_indi_043()
    fr_indi_044()
    fr_indi_045()
    fr_indi_046()
    fr_indi_047()
    fr_indi_048()
    fr_indi_049()
    fr_indi_085()
    speed = measure_market_speed(
        {
            "momentum": 1.0,
            "realized_volatility": 1.2,
            "range_expansion": 1.1,
            "volume_acceleration": 0.9,
            "order_flow_velocity": 1.0,
        },
        thresholds=(0.5, 1.5, 2.5),
    )
    envelope = measure_volatility_envelope(
        current=1.2,
        historical=1.0,
        operating_ratio=1.5,
        extreme_ratio=2.5,
    )
    print(f"Market-speed DATA: {speed.data}")
    print(f"Volatility-envelope DATA: {envelope.data}")


if __name__ == "__main__":
    main()
