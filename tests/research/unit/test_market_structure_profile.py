"""Unit tests for Research market-structure profile (FR-RES-075)."""

import pandas as pd
import pytest
from app.services.research import (
    DataQualityReport,
    MarketStructureConfig,
    MarketStructureProfile,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.market_structure import build_market_structure_profile
from app.utils import ValidationError, logger

_HASH = "e" * 64


def _prepared(rows: int = 30) -> PreparedDataset:
    """Build a PreparedDataset with trending OHLCVS data."""
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


def _config() -> MarketStructureConfig:
    """Build a market-structure configuration."""
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


def _limits() -> ResearchResourceLimits:
    """Build approved resource ceilings."""
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


def test_profile_reuses_canonical_score() -> None:
    """FR-RES-075: profile carries a canonical score and advisory fit."""
    logger.debug("Testing Research market-structure profile")
    profile = build_market_structure_profile(
        _prepared(), config=_config(), limits=_limits()
    )
    assert isinstance(profile, MarketStructureProfile)
    assert profile.schema_version == "v1"
    assert 0.0 <= profile.score <= 100.0
    assert profile.verdict in ("trending", "ranging", "mixed")
    assert profile.strategy_fit["advisory_only"] is True


def test_profile_rejects_oversized_input() -> None:
    """FR-RES-075: oversized input fails closed."""
    with pytest.raises(ValidationError, match="ROW_LIMIT_EXCEEDED"):
        build_market_structure_profile(
            _prepared(),
            config=_config(),
            limits=ResearchResourceLimits(5, 10.0, 1024),
        )
