"""Unit tests for Research validation and summaries (FR-RES-077, 078)."""

import pandas as pd
from app.services.research import MarketStructureConfig
from app.services.research.market_structure import (
    build_validation_summary,
    label_realized_market_behavior,
)
from app.utils import logger


def _config() -> MarketStructureConfig:
    """Build a market-structure configuration."""
    return MarketStructureConfig(
        {"swing_window": 5, "trend_threshold": 0.5, "range_threshold": 0.2},
        False,
        (10, 20),
        128,
        3,
    )


def _data(rows: int = 20) -> pd.DataFrame:
    """Build an OHLC frame with a close column."""
    idx = pd.date_range("2026-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series(
        [100.0 + i * 0.5 for i in range(rows)], index=idx, dtype="float64"
    )
    return pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close},
        index=idx,
    )


def test_label_behavior_uses_approved_horizon() -> None:
    """FR-RES-077: realized behavior is labeled under the approved horizon."""
    logger.debug("Testing Research realized behavior labeling")
    result = label_realized_market_behavior(
        _data(), symbol="TEST", timeframe="1h", config=_config()
    )
    assert result["schema_version"] == "v1"
    assert result["symbol"] == "TEST"
    assert result["verdict"] in ("trend", "reversion", "mixed", "insufficient")


def test_summary_preserves_sample_counts() -> None:
    """FR-RES-078: summary aggregates verdicts and sample counts."""
    logger.debug("Testing Research validation summary aggregation")
    result = build_validation_summary(
        [
            {"verdict": "trend", "symbol": "A", "confidence": 0.9},
            {"verdict": "reversion", "symbol": "B", "confidence": 0.8},
        ]
    )
    assert result["total_rows"] == 2
    assert result["by_verdict"]["trend"] == 1
    assert result["by_symbol"]["A"] == 1
