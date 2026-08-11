"""Executable usage evidence for FEAT-INDI-07 structure indicators."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.indicators import (
    anchored_vwap,
    donchian_channels,
    gaps,
    get_indicator_result_values,
    level_clustering,
    pivot_points,
    pivots,
    volume_profile,
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


def fr_indi_055() -> None:
    """FR-INDI-055: Stage 1 — Calculate confirmed swing pivots (IND-ST-01)."""
    _header("Stage 1: Structure confirmation - pivots formula execution (FR-INDI-055)")
    result = unwrap_indicator_response(pivots(_dataset(), left=2, right=2))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Pivot calculations")
    print_requirement_evidence("FR-INDI-055", actual_data=values)


def fr_indi_056() -> None:
    """FR-INDI-056: Stage 2 — Calculate Donchian channel levels (IND-ST-02)."""
    _header(
        "Stage 2: Structure channel contract - donchian_channels execution (FR-INDI-056)"
    )
    result = unwrap_indicator_response(donchian_channels(_dataset(), period=5))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Donchian-channel calculations")
    print_requirement_evidence("FR-INDI-056", actual_data=values)


def fr_indi_057() -> None:
    """FR-INDI-057: Stage 3 — Calculate Traditional pivot points (IND-ST-03)."""
    _header("Stage 3: Structure session levels - pivot_points execution (FR-INDI-057)")
    result = unwrap_indicator_response(pivot_points(_dataset()))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Pivot-points calculations")
    print_requirement_evidence("FR-INDI-057", actual_data=values)


def fr_indi_058() -> None:
    """FR-INDI-058: Stage 4 — Calculate Anchored VWAP (IND-ST-04)."""
    _header(
        "Stage 4: Structure reference price - anchored_vwap execution (FR-INDI-058)"
    )
    result = unwrap_indicator_response(anchored_vwap(_dataset(), anchor_index=0))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Anchored-VWAP calculations")
    print_requirement_evidence("FR-INDI-058", actual_data=values)


def fr_indi_059() -> None:
    """FR-INDI-059: Stage 5 — Calculate rolling volume-profile POC/VA (IND-ST-05)."""
    _header(
        "Stage 5: Structure distribution contract - volume_profile execution "
        "(FR-INDI-059)"
    )
    result = unwrap_indicator_response(volume_profile(_dataset(), period=10, bins=5))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Volume-profile calculations")
    print_requirement_evidence("FR-INDI-059", actual_data=values)


def fr_indi_060() -> None:
    """FR-INDI-060: Stage 6 — Calculate price gaps and fair-value gaps (IND-ST-06)."""
    _header("Stage 6: Structure discontinuity - gaps formula execution (FR-INDI-060)")
    result = unwrap_indicator_response(gaps(_dataset(), min_gap=0.0001))
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Gap calculations")
    print_requirement_evidence("FR-INDI-060", actual_data=values)


def fr_indi_061() -> None:
    """FR-INDI-061: Stage 7 — Calculate structural-level clustering (IND-ST-07)."""
    _header("Stage 7: Structure aggregation - level_clustering execution (FR-INDI-061)")
    result = unwrap_indicator_response(
        level_clustering(_dataset(), lookback=10, tolerance=0.001, half_life=5.0)
    )
    values = get_indicator_result_values(result)
    print(_format_result(result))
    print(f"Data -> rows={len(values)}, columns={list(values.columns)}")
    print_indicator_evidence(result, label="Level-clustering calculations")
    print_requirement_evidence("FR-INDI-061", actual_data=values)


def main() -> None:
    """Run every structure requirement demonstration."""
    _feature_header(
        "FEATURE: FEAT-INDI-07 — structure/ — Support, Resistance, and "
        "Structural Levels\n\n"
        "Purpose: Compute the approved structural-level indicators through "
        "stateless vectorized batch functions.\n\n"
        "Module flow:\n"
        "-> normalized OHLC/volume values\n"
        "-> Core validation\n"
        "-> approved structure formula\n"
        "-> IndicatorResult"
    )

    try:
        _dataset()
    except RuntimeError as unavailable:
        print(f"Skipping structure examples: MT5 data unavailable ({unavailable.code})")
        raise SystemExit(3) from None

    print_market_evidence(_dataset())
    fr_indi_055()
    fr_indi_056()
    fr_indi_057()
    fr_indi_058()
    fr_indi_059()
    fr_indi_060()
    fr_indi_061()


if __name__ == "__main__":
    main()
