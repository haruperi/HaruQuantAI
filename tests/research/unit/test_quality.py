"""Unit tests for Research market-structure quality (FR-RES-076)."""

import pandas as pd
from app.services.research import (
    create_research_value,
    evaluate_market_structure_quality,
    is_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)

_HASH = "e" * 64


def _prepared(rows: int = 30) -> object:
    """Build a PreparedDataset with OHLCVS data."""
    idx = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series(
        [100.0 + i * 0.5 for i in range(rows)], index=idx, dtype="float64"
    )
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


def _limits() -> object:
    """Build approved resource ceilings."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def test_quality_is_opt_in_and_bounded() -> None:
    """FR-RES-076: quality is opt-in and disabled returns a warning."""
    logger.debug("Testing Research market-structure quality opt-in")
    config = create_research_value(
        "MarketStructureConfig",
        {"swing_window": 5, "trend_threshold": 0.5, "range_threshold": 0.2},
        False,
        (10, 20),
        128,
        5,
    )
    report = evaluate_market_structure_quality(
        _prepared(), config=config, limits=_limits()
    )
    assert is_research_value(report, "MarketStructureQualityReport")
    assert report.warnings
    assert any(w.code == "QUALITY_DISABLED" for w in report.warnings)


def test_quality_enabled_produces_stability_windows() -> None:
    """FR-RES-076: enabled quality produces stability evidence."""
    config = create_research_value(
        "MarketStructureConfig",
        {"swing_window": 5, "trend_threshold": 0.5, "range_threshold": 0.2},
        True,
        (10, 20),
        128,
        5,
    )
    report = evaluate_market_structure_quality(
        _prepared(rows=30), config=config, limits=_limits()
    )
    assert "windows" in report.stability
