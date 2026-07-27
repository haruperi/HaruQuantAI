"""Integration evidence for WF-RES-006: market-structure profile and fit."""

import pandas as pd
from app.services.research import (
    DataQualityReport,
    MarketStructureConfig,
    MarketStructureProfile,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.market_structure import (
    build_market_structure_profile,
    build_strategy_fit,
)
from app.utils import logger

_HASH = "e" * 64


def _prepared() -> PreparedDataset:
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
    return PreparedDataset(
        frame,
        "v1",
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )


def _config() -> MarketStructureConfig:
    """Build market-structure settings."""
    return MarketStructureConfig(
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
        limits=ResearchResourceLimits(500_000, 600.0, 52_428_800),
    )
    fit = build_strategy_fit(profile)
    assert isinstance(profile, MarketStructureProfile)
    assert profile.strategy_fit["advisory_only"] is True
    assert fit["advisory_only"] is True
    assert fit["score"] == profile.score
