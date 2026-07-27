"""Unit tests for Research market-structure quality (FR-RES-076)."""

import pandas as pd
from app.services.research import (
    DataQualityReport,
    MarketStructureConfig,
    MarketStructureQualityReport,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.market_structure import (
    evaluate_market_structure_quality,
)
from app.utils import logger

_HASH = "e" * 64


def _prepared(rows: int = 30) -> PreparedDataset:
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
    return PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )


def _limits() -> ResearchResourceLimits:
    """Build approved resource ceilings."""
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


def test_quality_is_opt_in_and_bounded() -> None:
    """FR-RES-076: quality is opt-in and disabled returns a warning."""
    logger.debug("Testing Research market-structure quality opt-in")
    config = MarketStructureConfig(
        {"swing_window": 5, "trend_threshold": 0.5, "range_threshold": 0.2},
        False,
        (10, 20),
        128,
        5,
    )
    report = evaluate_market_structure_quality(
        _prepared(), config=config, limits=_limits()
    )
    assert isinstance(report, MarketStructureQualityReport)
    assert report.warnings
    assert any(w.code == "QUALITY_DISABLED" for w in report.warnings)


def test_quality_enabled_produces_stability_windows() -> None:
    """FR-RES-076: enabled quality produces stability evidence."""
    config = MarketStructureConfig(
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
