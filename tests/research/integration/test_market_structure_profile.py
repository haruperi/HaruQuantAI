"""Integration evidence for WF-RES-006: market-structure profile and fit."""

import pandas as pd
from app.services.research import (
    build_market_structure_profile,
    build_strategy_fit,
    create_research_value,
    is_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)

_HASH = "e" * 64


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
        },
        False,
        (10, 20),
        128,
        5,
    )


def test_profile_and_fit_share_canonical_score() -> None:
    """WF-RES-006: profile and fit share the canonical structure score."""
    logger.debug("Testing Research market-structure profile and fit integration")
    profile = build_market_structure_profile(
        _prepared(),
        config=_config(),
        limits=create_research_value(
            "ResearchResourceLimits", 500_000, 600.0, 52_428_800
        ),
    )
    fit = build_strategy_fit(profile)
    assert is_research_value(profile, "MarketStructureProfile")
    assert profile.strategy_fit["advisory_only"] is True
    assert fit["advisory_only"] is True
    assert fit["score"] == profile.score
