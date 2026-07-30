"""Unit tests for Research market-structure profile (FR-RES-075)."""

import pandas as pd
import pytest
from app.services.research import (
    build_market_structure_profile,
    create_research_value,
    is_research_value,
)
from app.utils import get_logger

logger = get_logger(__name__)

_HASH = "e" * 64


def _prepared(rows: int = 30) -> object:
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
    """Build a market-structure configuration."""
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


def _limits() -> object:
    """Build approved resource ceilings."""
    return create_research_value("ResearchResourceLimits", 500_000, 600.0, 52_428_800)


def test_profile_reuses_canonical_score() -> None:
    """FR-RES-075: profile carries a canonical score and advisory fit."""
    logger.debug("Testing Research market-structure profile")
    profile = build_market_structure_profile(
        _prepared(), config=_config(), limits=_limits()
    )
    assert is_research_value(profile, "MarketStructureProfile")
    assert profile.schema_version == "v1"
    assert 0.0 <= profile.score <= 100.0
    assert profile.verdict in ("trending", "ranging", "mixed")
    assert profile.strategy_fit["advisory_only"] is True


def test_profile_rejects_oversized_input() -> None:
    """FR-RES-075: oversized input fails closed."""
    with pytest.raises(ValueError, match="ROW_LIMIT_EXCEEDED"):
        build_market_structure_profile(
            _prepared(),
            config=_config(),
            limits=create_research_value("ResearchResourceLimits", 5, 10.0, 1024),
        )


def test_profile_handles_insufficient_range_and_missing_ohlc() -> None:
    """Cover bounded insufficiency, ranging evidence, and column refusal."""
    insufficient = build_market_structure_profile(
        _prepared(3),
        config=_config(),
        limits=_limits(),
    )
    assert insufficient.warnings[0].code == "INSUFFICIENT_SAMPLES"

    prepared = _prepared()
    prepared.data.loc[:, "close"] = 100.0
    ranging = build_market_structure_profile(
        prepared,
        config=_config(),
        limits=_limits(),
    )
    assert ranging.verdict == "ranging"
    assert ranging.strategy_fit["primary_archetype"] == "mean_revert"

    missing = create_research_value(
        "PreparedDataset",
        prepared.data.drop(columns=["close"]),
        "v1",
        create_research_value("DataQualityReport", (), (), ("schema",), ()),
        _HASH,
        _HASH,
        ("fixture",),
    )
    with pytest.raises(ValueError, match="OHLC_COLUMNS_REQUIRED"):
        build_market_structure_profile(
            missing,
            config=_config(),
            limits=_limits(),
        )
