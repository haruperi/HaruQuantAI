"""Executable usage evidence for volatility indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import get_market_data
from app.services.indicators import (
    adr,
    atr,
    get_indicator_result_values,
    measure_market_speed,
    measure_volatility_envelope,
    rolling_volatility,
    standard_deviation,
)
from tests.indicators.usage._support import (
    print_indicator_evidence,
    print_market_evidence,
    print_requirement_evidence,
    unwrap_indicator_response,
    unwrap_market_data_response,
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


def _dataset(timeframe: str) -> MarketDataset:
    """Return one cached real read-only market dataset."""

    if timeframe not in _CACHE:
        _CACHE[timeframe] = unwrap_market_data_response(
            get_market_data(
                source_id="mt5",
                symbol="EURUSD",
                timeframe=timeframe,
                limit=20,
            )
        )
    return _CACHE[timeframe]


def fr_indi_018() -> None:
    """FR-INDI-018: Stage 1 — Calculate ATR from approved range contract."""
    _header("Stage 1: Volatility range contract - ATR formula execution (FR-INDI-018)")
    result = unwrap_indicator_response(atr(_dataset("M5"), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="ATR calculations")
    print_requirement_evidence("FR-INDI-018", actual_data=values)


def fr_indi_019() -> None:
    """FR-INDI-019: Stage 2 — Calculate ADR on deterministic D1 ranges."""
    _header("Stage 2: Range mean contract - ADR formula execution (FR-INDI-019)")
    result = unwrap_indicator_response(adr(_dataset("D1"), period=2))
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
    result = unwrap_indicator_response(rolling_volatility(_dataset("M5"), period=2))
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
    result = unwrap_indicator_response(standard_deviation(_dataset("M5"), period=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Standard-deviation calculations")
    print_requirement_evidence("FR-INDI-026", actual_data=values)


def main() -> None:
    """Run every volatility requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-05 — volatility/ — Volatility and Range Calculation\n\n"
        "Purpose: Compute approved range- and return-based volatility measures.\n\n"
        "Module flow:\n"
        "-> normalized OHLC/source values\n"
        "-> Core validation\n"
        "-> approved volatility formula\n"
        "-> IndicatorResult"
    )

    try:
        _dataset("M5")
        _dataset("D1")
    except RuntimeError as unavailable:
        print(
            f"Skipping volatility examples: MT5 data unavailable ({unavailable.code})"
        )
        raise SystemExit(3) from None

    print_market_evidence(_dataset("M5"))
    print_market_evidence(_dataset("D1"))
    fr_indi_018()
    fr_indi_019()
    fr_indi_020()
    fr_indi_026()
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
