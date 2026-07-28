"""Deterministic market-structure profile and canonical scoring for Research."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from app.services.research.contracts import (
    MarketStructureProfile,
    ResearchWarning,
)
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import (
        MarketStructureConfig,
        PreparedDataset,
        ResearchResourceLimits,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def _atr(data: pd.DataFrame, period: int) -> float:
    """Compute the average true range over OHLC data.

    Args:
        data: Frame with high, low, and close columns.
        period: Positive lookback window.

    Returns:
        The mean true range, or 0.0 when insufficient.

    Raises:
        ValueError: If OHLC columns are absent.
    """
    if not {"high", "low", "close"} <= set(data.columns):
        raise ValueError("RES_INPUT_INVALID", "OHLC_COLUMNS_REQUIRED")
    high = data["high"].astype("float64")
    low = data["low"].astype("float64")
    prev_close = data["close"].shift(1).astype("float64")
    true_range = pd.concat(
        [(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    usable = true_range.dropna()
    if usable.empty or period <= 0:
        return 0.0
    return float(usable.tail(period).mean())


def canonical_structure_score(
    *, efficiency_ratio: float, trend_threshold: float, range_threshold: float
) -> float:
    """Map an efficiency ratio to the canonical 0-100 structure score.

    Args:
        efficiency_ratio: Absolute net displacement over total path in [0, 1].
        trend_threshold: Ratio at or above which the market is trending.
        range_threshold: Ratio at or below which the market is ranging.

    Returns:
        Canonical score in [0, 100].
    """
    ratio = max(0.0, min(1.0, abs(efficiency_ratio)))
    if ratio >= trend_threshold:
        return 100.0
    if ratio <= range_threshold:
        return 0.0
    span = trend_threshold - range_threshold
    if span <= 0:
        return 50.0
    return 100.0 * (ratio - range_threshold) / span


def _verdict(score: float, trend_threshold: float, range_threshold: float) -> str:
    """Classify the canonical score into a regime verdict.

    Args:
        score: Canonical structure score in [0, 100].
        trend_threshold: Score at or above which trending is declared.
        range_threshold: Score at or below which ranging is declared.

    Returns:
        One of ``trending``, ``ranging``, or ``mixed``.
    """
    if score >= 100.0 * trend_threshold:
        return "trending"
    if score <= 100.0 * range_threshold:
        return "ranging"
    return "mixed"


def _strategy_fit(verdict_label: str, score: float) -> Mapping[str, JSONValue]:
    """Produce advisory archetype fit evidence from the verdict.

    Args:
        verdict_label: Canonical regime verdict.
        score: Canonical structure score.

    Returns:
        Advisory archetype ranking (advisory-only, no approval).
    """
    if verdict_label == "trending":
        primary = "trend_follow"
    elif verdict_label == "ranging":
        primary = "mean_revert"
    else:
        primary = "range"
    return {
        "primary_archetype": primary,
        "score": score,
        "advisory_only": True,
    }


def build_market_structure_profile(
    prepared: PreparedDataset,
    *,
    config: MarketStructureConfig,
    limits: ResearchResourceLimits,
) -> MarketStructureProfile:
    """Build swings, directional evidence, canonical score, verdict, and fit.

    Args:
        prepared: Prepared Research dataset.
        config: Bounded market-structure settings.
        limits: Approved resource ceilings.

    Returns:
        Canonical advisory ``MarketStructureProfile``.

    Raises:
        ValueError: If data, configuration, or resources are invalid.
    """
    logger.info("Building Research market-structure profile")
    if len(prepared.data) > limits.max_rows:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", "ROW_LIMIT_EXCEEDED")
    settings = config.profile
    swing_window = int(settings.get("swing_window", 5))  # type: ignore[arg-type]
    atr_period = int(settings.get("atr_period", 14))  # type: ignore[arg-type]
    trend_threshold = float(settings.get("trend_threshold", 0.5))  # type: ignore[arg-type]
    range_threshold = float(settings.get("range_threshold", 0.2))  # type: ignore[arg-type]
    if not {"high", "low", "close"} <= set(prepared.data.columns):
        raise ValueError("RES_INPUT_INVALID", "OHLC_COLUMNS_REQUIRED")
    close = prepared.data["close"].astype("float64")
    if len(close) < swing_window:
        return _insufficient_profile(prepared)
    atr_value = _atr(prepared.data, atr_period)
    net_displacement = abs(float(close.iloc[-1] - close.iloc[0]))
    total_path = float(close.diff().abs().sum())
    efficiency_ratio = net_displacement / total_path if total_path > 0 else 0.0
    score = canonical_structure_score(
        efficiency_ratio=efficiency_ratio,
        trend_threshold=trend_threshold,
        range_threshold=range_threshold,
    )
    verdict_label = _verdict(score, trend_threshold, range_threshold)
    structure: dict[str, JSONValue] = {
        "swing_window": swing_window,
        "atr_period": atr_period,
        "atr": atr_value,
        "efficiency_ratio": efficiency_ratio,
        "trend_threshold": trend_threshold,
        "range_threshold": range_threshold,
    }
    return MarketStructureProfile(
        "v1",
        structure,
        score,
        verdict_label,
        _strategy_fit(verdict_label, score),
        (),
    )


def _insufficient_profile(
    prepared: PreparedDataset,
) -> MarketStructureProfile:
    """Build an inconclusive profile recording documented insufficiency.

    Args:
        prepared: Prepared Research dataset.

    Returns:
        Advisory inconclusive ``MarketStructureProfile`` with a warning.
    """
    warning = ResearchWarning(
        "INSUFFICIENT_SAMPLES",
        "Market-structure profile data below the declared swing window",
        "warning",
        "structure",
        {"row_count": len(prepared.data)},
    )
    return MarketStructureProfile(
        "v1",
        {"row_count": len(prepared.data)},
        0.0,
        "ranging",
        {"primary_archetype": "range", "score": 0.0, "advisory_only": True},
        (warning,),
    )


__all__ = (
    "build_market_structure_profile",
    "canonical_structure_score",
)
