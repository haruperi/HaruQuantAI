"""Unit tests for Research validation and summaries (FR-RES-077, 078)."""

import pandas as pd
import pytest
from app.composition.logging import get_logger
from app.services.research import (
    build_validation_summary,
    create_research_value,
    label_realized_market_behavior,
)

logger = get_logger(__name__)


def _config() -> object:
    """Build a market-structure configuration."""
    return create_research_value(
        "MarketStructureConfig",
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


def test_labeling_and_summary_fail_closed_and_preserve_missingness() -> None:
    """Cover identity, schema, insufficiency, and summary fallback branches."""
    with pytest.raises(ValueError, match="INVALID_IDENTITY"):
        label_realized_market_behavior(
            _data(),
            symbol=" ",
            timeframe="1h",
            config=_config(),
        )
    with pytest.raises(ValueError, match="CLOSE_COLUMN_REQUIRED"):
        label_realized_market_behavior(
            _data().drop(columns=["close"]),
            symbol="TEST",
            timeframe="1h",
            config=_config(),
        )
    insufficient = label_realized_market_behavior(
        _data(2),
        symbol="TEST",
        timeframe="1h",
        config=_config(),
    )
    assert insufficient["verdict"] == "insufficient"
    with pytest.raises(ValueError, match="EMPTY_VALIDATION_ROWS"):
        build_validation_summary([])
    summary = build_validation_summary(
        [{"verdict": "unknown", "symbol": "A", "confidence": True}]
    )
    assert summary["by_verdict"]["mixed"] == 1
    assert summary["mean_confidence"] == 0.0
