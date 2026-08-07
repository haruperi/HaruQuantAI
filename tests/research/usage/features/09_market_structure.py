"""Executable Research market-structure usage example.

Demonstrates profile, quality, validation, calibration, and strategy fit.
"""

import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import (
    build_market_structure_profile,
    build_strategy_fit,
    build_validation_summary,
    calibrate_market_structure,
    create_research_value,
    evaluate_market_structure_quality,
    label_realized_market_behavior,
)

_HASH = "e" * 64


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"SUCCESS: {title}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"SUCCESS: {title}")


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


def _prepared() -> object:
    """Build a PreparedDataset with trending OHLCVS data."""
    idx = pd.date_range("2026-01-05", periods=30, freq="h", tz="UTC")
    close = pd.Series([100.0 + i * 0.5 for i in range(30)], index=idx, dtype="float64")
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 100.0,
            "spread": 0.1,
        },
        index=idx,
    )
    return create_research_value(
        "PreparedDataset",
        frame,
        "v1",
        create_research_value("DataQualityReport", (), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )


def _config() -> object:
    """Build market-structure settings."""
    return create_research_value(
        "MarketStructureConfig",
        {
            "swing_window": 5,
            "atr_period": 14,
            "trend_threshold": 0.5,
            "range_threshold": 0.2,
            "calibration_grid": [{"trend_threshold": 0.4}],
        },
        True,
        (10, 20),
        128,
        5,
    )


def _limits() -> object:
    """Build approved resource ceilings."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def fr_res_075() -> None:
    """FR-RES-075: Build swings, directional legs, score, verdict, and fit."""
    _header("FR-RES-075: Build swings, directional legs, score, verdict, and fit.")
    profile = build_market_structure_profile(
        _prepared(), config=_config(), limits=_limits()
    )
    print(f"FR-RES-075 verdict={profile.verdict} score={profile.score}")


def fr_res_076() -> None:
    """FR-RES-076: Run bounded temporal stability and parameter robustness."""
    _header("FR-RES-076: Run bounded temporal stability and parameter robustness.")
    report = evaluate_market_structure_quality(
        _prepared(), config=_config(), limits=_limits()
    )
    windows = report.stability.get("windows", [])
    print(f"FR-RES-076 stability_windows={len(windows)}")


def fr_res_077() -> None:
    """FR-RES-077: Label later bars as trend/reversion/mixed."""
    _header("FR-RES-077: Label later bars as trend/reversion/mixed.")
    result = label_realized_market_behavior(
        _prepared().data, symbol="TEST", timeframe="1h", config=_config()
    )
    print(f"FR-RES-077 verdict={result['verdict']}")


def fr_res_078() -> None:
    """FR-RES-078: Return concise observation/uncertainty/readiness summary."""
    _header("FR-RES-078: Return concise observation/uncertainty/readiness summary.")
    summary = build_validation_summary(
        [{"verdict": "trend", "symbol": "TEST", "confidence": 0.9}]
    )
    print(f"FR-RES-078 total_rows={summary['total_rows']}")


def fr_res_079() -> None:
    """FR-RES-079: Rank calibration candidates by canonical score."""
    _header("FR-RES-079: Rank calibration candidates by canonical score.")
    result = calibrate_market_structure(
        run_rows=[
            {"efficiency_ratio": 0.6, "verdict": "trend", "symbol": "TEST"},
        ],
        validation_rows=[{"symbol": "TEST", "verdict": "trend"}],
        config=_config(),
        limits=_limits(),
    )
    print(f"FR-RES-079 candidates={result['candidate_count']}")


def fr_res_080() -> None:
    """FR-RES-080: Rank advisory strategy archetypes from profile evidence."""
    _header("FR-RES-080: Rank advisory strategy archetypes from profile evidence.")
    profile = create_research_value(
        "MarketStructureProfile",
        "v1",
        {"swing_window": 5},
        75.0,
        "trending",
        {"primary_archetype": "trend_follow", "advisory_only": True},
        (),
    )
    fit = build_strategy_fit(profile)
    print(f"FR-RES-080 archetype={fit['primary_archetype']}")


def main() -> None:
    """Run Research market-structure usage example."""
    _feature_header(
        "FEATURE: FEAT-RES-09 — market_structure/ — Market Structure Analysis\n\n"
        "Purpose: Profile volatility regimes, regime stability, calibration quality, and strategy fit.\n\n"
        "Module flow:\n"
        "-> Stage 1: Volatility regime tagging and profile extraction\n-> Stage 2: Regime transition stability and forward robustness testing\n-> Stage 3: Strategy fit recommendation rendering"
    )

    fr_res_075()
    fr_res_076()
    fr_res_077()
    fr_res_078()
    fr_res_079()
    fr_res_080()


if __name__ == "__main__":
    main()
