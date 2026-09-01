"""Deterministic market-structure profile and canonical scoring for Research."""

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING, TypedDict, cast

import pandas as pd

from app.composition.logging import get_logger
from app.services.research.contracts import (
    MarketStructureProfile,
    ResearchWarning,
)

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

_MAX_GEOMETRY_POINTS = 256


class _SwingPoint(TypedDict):
    """Typed internal swing candidate before JSON projection."""

    position: int
    timestamp: str
    kind: str
    price: float


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


def _timestamp(value: object) -> str:
    """Return a stable timestamp label for one frame index value.

    Args:
        value: DataFrame index value.

    Returns:
        ISO timestamp when supported, otherwise its bounded string form.
    """
    isoformat = getattr(value, "isoformat", None)
    return str(isoformat()) if callable(isoformat) else str(value)


def _collapse_swing_candidate(
    points: list[_SwingPoint], candidate: _SwingPoint
) -> None:
    """Append an alternating swing or retain the more extreme same-kind point.

    Exact ties retain the later candidate so every collapse is deterministic.

    Args:
        points: Mutable ordered swing series.
        candidate: Candidate high or low point.
    """
    if not points or points[-1]["kind"] != candidate["kind"]:
        points.append(candidate)
        return
    previous_price = float(points[-1]["price"])
    candidate_price = float(candidate["price"])
    more_extreme = (
        candidate_price >= previous_price
        if candidate["kind"] == "high"
        else candidate_price <= previous_price
    )
    if more_extreme:
        points[-1] = candidate


def _swing_points(data: pd.DataFrame, *, radius: int) -> list[_SwingPoint]:
    """Detect confirmed centered-window swing highs and lows.

    Centered confirmation deliberately uses later observations. These points
    are descriptive Research evidence and must not be treated as online trading
    signals.

    Args:
        data: Ordered OHLC frame.
        radius: Bars required on each side of a confirmed extremum.

    Returns:
        Ordered alternating swing-point records.
    """
    window = 2 * radius + 1
    high = data["high"].astype("float64")
    low = data["low"].astype("float64")
    rolling_high = high.rolling(window, center=True, min_periods=window).max()
    rolling_low = low.rolling(window, center=True, min_periods=window).min()
    points: list[_SwingPoint] = []
    for position in range(radius, len(data) - radius):
        is_high = bool(high.iloc[position] == rolling_high.iloc[position])
        is_low = bool(low.iloc[position] == rolling_low.iloc[position])
        if is_high == is_low:
            continue
        kind = "high" if is_high else "low"
        price = high.iloc[position] if is_high else low.iloc[position]
        _collapse_swing_candidate(
            points,
            {
                "position": position,
                "timestamp": _timestamp(data.index[position]),
                "kind": kind,
                "price": float(price),
            },
        )
    return points


def _trend_legs(points: list[_SwingPoint], *, atr_value: float) -> list[JSONValue]:
    """Connect consecutive alternating swings into directional legs.

    Args:
        points: Ordered bounded swing series.
        atr_value: Profile ATR used only for normalized magnitude evidence.

    Returns:
        Ordered directional leg records.
    """
    legs: list[JSONValue] = []
    for start, end in pairwise(points):
        start_price = float(start["price"])
        end_price = float(end["price"])
        change = end_price - start_price
        legs.append(
            {
                "start_position": int(start["position"]),
                "end_position": int(end["position"]),
                "start_timestamp": str(start["timestamp"]),
                "end_timestamp": str(end["timestamp"]),
                "start_price": start_price,
                "end_price": end_price,
                "direction": "up" if change > 0 else "down",
                "bar_count": int(end["position"]) - int(start["position"]),
                "price_change": change,
                "absolute_change": abs(change),
                "atr_multiple": abs(change) / atr_value if atr_value > 0 else None,
            }
        )
    return legs


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
    detected_points = _swing_points(prepared.data, radius=swing_window)
    geometry_total_points = len(detected_points)
    swing_points = detected_points[-_MAX_GEOMETRY_POINTS:]
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
        "swing_points": [cast("JSONValue", dict(point)) for point in swing_points],
        "trend_legs": _trend_legs(swing_points, atr_value=atr_value),
        "geometry_point_limit": _MAX_GEOMETRY_POINTS,
        "geometry_total_points": geometry_total_points,
        "geometry_truncated": geometry_total_points > len(swing_points),
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
