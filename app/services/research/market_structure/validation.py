"""Realized market-behavior labeling and validation summaries for Research."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from app.composition.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from app.services.research.contracts import MarketStructureConfig

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_VERDICTS = ("trend", "reversion", "mixed")


def label_realized_market_behavior(
    data: pd.DataFrame,
    *,
    symbol: str,
    timeframe: str,
    config: MarketStructureConfig,
) -> Mapping[str, JSONValue]:
    """Label later bars as trend/reversion/mixed under one truth policy.

    Args:
        data: OHLC frame with a close column.
        symbol: Canonical symbol identity.
        timeframe: Declared timeframe.
        config: Bounded market-structure settings with validation_horizon.

    Returns:
        Versioned realized-behavior evidence with insufficiency warnings.

    Raises:
        ValueError: If the truth policy or data is invalid.
    """
    logger.info("Labeling Research realized market behavior")
    horizon = config.validation_horizon
    if horizon <= 0:
        raise ValueError("RES_INPUT_INVALID", "INVALID_VALIDATION_HORIZON")
    if not symbol.strip() or not timeframe.strip():
        raise ValueError("RES_INPUT_INVALID", "INVALID_IDENTITY")
    if "close" not in data.columns:
        raise ValueError("RES_INPUT_INVALID", "CLOSE_COLUMN_REQUIRED")
    close = data["close"].astype("float64")
    if len(close) <= horizon:
        return {
            "schema_version": "v1",
            "symbol": symbol,
            "timeframe": timeframe,
            "horizon": horizon,
            "verdict": "insufficient",
            "sample_count": 0,
            "warnings": ["INSUFFICIENT_SAMPLES"],
        }
    future = close.shift(-horizon)
    forward_return = (future - close) / close
    volatility = close.pct_change().rolling(horizon).std()
    valid = forward_return.dropna()
    if valid.empty:
        return {
            "schema_version": "v1",
            "symbol": symbol,
            "timeframe": timeframe,
            "horizon": horizon,
            "verdict": "insufficient",
            "sample_count": 0,
            "warnings": ["INSUFFICIENT_SAMPLES"],
        }
    median_vol = (
        float(volatility.dropna().median()) if not volatility.dropna().empty else 0.0
    )
    directional = abs(float(valid.mean()))
    if directional > median_vol:
        verdict = "trend"
    elif directional < median_vol * 0.3:
        verdict = "reversion"
    else:
        verdict = "mixed"
    return {
        "schema_version": "v1",
        "symbol": symbol,
        "timeframe": timeframe,
        "horizon": horizon,
        "verdict": verdict,
        "sample_count": int(valid.size),
        "mean_forward_return": float(valid.mean()),
        "median_volatility": median_vol,
    }


def build_validation_summary(
    rows: Sequence[Mapping[str, JSONValue]],
) -> Mapping[str, JSONValue]:
    """Aggregate prediction evidence by confidence, verdict, and identity.

    Args:
        rows: Sequence of prediction-row mappings carrying verdict/confidence.

    Returns:
        Versioned summary with per-verdict and per-symbol sample counts.

    Raises:
        ValueError: If rows are empty or malformed.
    """
    logger.debug("Building Research validation summary")
    if not rows:
        raise ValueError("RES_INPUT_INVALID", "EMPTY_VALIDATION_ROWS")
    by_verdict: dict[str, int] = dict.fromkeys(_VERDICTS, 0)
    by_symbol: dict[str, int] = {}
    confidence_values: list[float] = []
    for row in rows:
        verdict = str(row.get("verdict", "mixed"))
        if verdict not in _VERDICTS:
            verdict = "mixed"
        by_verdict[verdict] = by_verdict.get(verdict, 0) + 1
        symbol = str(row.get("symbol", "unknown"))
        by_symbol[symbol] = by_symbol.get(symbol, 0) + 1
        confidence = row.get("confidence")
        if isinstance(confidence, int | float) and not isinstance(confidence, bool):
            confidence_values.append(float(confidence))
    mean_confidence = (
        sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    )
    return {
        "schema_version": "v1",
        "total_rows": len(rows),
        "by_verdict": by_verdict,
        "by_symbol": by_symbol,
        "mean_confidence": mean_confidence,
    }


__all__ = ("build_validation_summary", "label_realized_market_behavior")
