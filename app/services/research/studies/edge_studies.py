"""Deterministic mean-reversion, trend-persistence, and session edge studies.

Each study evaluates one advisory hypothesis on declared split data against a
matched seeded null and records uncertainty, confirmation policy, and warnings.
No study authorizes, mutates, or invents live evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Literal, cast

import numpy as np
import pandas as pd

from app.composition.logging import get_logger
from app.services.research.contracts import EdgeResult, ResearchWarning
from app.services.research.features import forward_returns
from app.services.research.statistics import (
    benjamini_hochberg,
    compute_null_percentile,
    exceeds_null_threshold,
    null_distribution_stats,
    random_entry_null,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.research.contracts import (
        ResearchResourceLimits,
        StatisticalConfig,
        StudyConfig,
        TimeSplitResult,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def _int_setting(mapping: Mapping[str, JSONValue], key: str, detail: str) -> int:
    """Extract one required positive-integer study setting.

    Args:
        mapping: Closed study-policy mapping.
        key: Required setting key.
        detail: Symbolic error detail.

    Returns:
        The validated positive integer.

    Raises:
        ValueError: If the setting is absent or not a positive integer.
    """
    value = mapping.get(key)
    # Booleans are ints in Python; exclude them explicitly.
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError("RES_INPUT_INVALID", detail)
    return value


def _float_setting(mapping: Mapping[str, JSONValue], key: str, detail: str) -> float:
    """Extract one required finite study setting.

    Args:
        mapping: Closed study-policy mapping.
        key: Required setting key.
        detail: Symbolic error detail.

    Returns:
        The validated finite float.

    Raises:
        ValueError: If the setting is absent or non-finite.
    """
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(  # noqa: TRY004 - Research validation taxonomy.
            "RES_INPUT_INVALID", detail
        )
    output = float(value)
    if not np.isfinite(output):
        raise ValueError("RES_INPUT_INVALID", detail)
    return output


def _unit_interval_setting(
    mapping: Mapping[str, JSONValue], key: str, detail: str
) -> float:
    """Extract one required open-unit-interval study setting.

    Args:
        mapping: Closed study-policy mapping.
        key: Required setting key.
        detail: Symbolic error detail.

    Returns:
        The validated value in the open unit interval.

    Raises:
        ValueError: If the setting is outside ``(0, 1)``.
    """
    output = _float_setting(mapping, key, detail)
    if not 0.0 < output < 1.0:
        raise ValueError("RES_INPUT_INVALID", detail)
    return output


def _side_setting(
    mapping: Mapping[str, JSONValue], detail: str
) -> Literal["buy", "sell"]:
    """Extract one required directional side setting.

    Args:
        mapping: Closed study-policy mapping.
        detail: Symbolic error detail.

    Returns:
        The validated buy or sell side.

    Raises:
        ValueError: If the side is not buy or sell.
    """
    value = mapping.get("side")
    if value not in ("buy", "sell"):
        raise ValueError("RES_INPUT_INVALID", detail)
    return cast("Literal['buy', 'sell']", value)


def _enforce_rows(
    data: pd.DataFrame, limits: ResearchResourceLimits, detail: str
) -> None:
    """Reject oversized input before any computation.

    Args:
        data: Candidate frame.
        limits: Approved resource ceilings.
        detail: Symbolic error detail.

    Raises:
        ValueError: If the row count exceeds the approved limit.
    """
    logger.debug("Checking Research edge-study resource limits")
    if len(data) > limits.max_rows:
        raise ValueError("RES_RESOURCE_LIMIT_EXCEEDED", detail)


def _classify(
    observed: float,
    distribution: np.ndarray,
    side: Literal["buy", "sell"],
    quantile: float,
) -> str:
    """Classify one observed edge statistic against its matched null.

    Args:
        observed: Finite observed mean statistic.
        distribution: Finite matched null distribution.
        side: Declared study side.
        quantile: Null exceedance quantile.

    Returns:
        ``confirmed``, ``contradicted``, or ``inconclusive``.
    """
    expected = "upper" if side == "buy" else "lower"
    if exceeds_null_threshold(
        observed, distribution, quantile=quantile, alternative=expected
    ):
        return "confirmed"
    opposite = "lower" if side == "buy" else "upper"
    if exceeds_null_threshold(
        observed, distribution, quantile=quantile, alternative=opposite
    ):
        return "contradicted"
    return "inconclusive"


def _mean_reversion_entries(
    zscores: pd.Series, side: Literal["buy", "sell"], entry_zscore: float
) -> pd.Series:
    """Select fade entries where the z-score exceeds the declared threshold.

    Args:
        zscores: Rolling close z-scores.
        side: Buy fades oversold bars; sell fades overbought bars.
        entry_zscore: Positive deviation threshold.

    Returns:
        Boolean alignment of selected entry bars.
    """
    if side == "buy":
        return zscores <= -entry_zscore
    return zscores >= entry_zscore


def _trend_breakout_entries(
    close: pd.Series,
    lookback: int,
    minimum_move: float,
    side: Literal["buy", "sell"],
) -> pd.Series:
    """Select breakout entries whose lookback move exceeds the threshold.

    Args:
        close: Finite close prices.
        lookback: Positive move-measurement window.
        minimum_move: Positive minimum fractional move.
        side: Buy selects up-breakouts; sell selects down-breakouts.

    Returns:
        Boolean alignment of selected breakout bars.
    """
    move = close.pct_change(lookback)
    if side == "buy":
        return move >= minimum_move
    return move <= -minimum_move


def run_eds_mean_reversion(
    data: pd.DataFrame,
    *,
    split: TimeSplitResult,
    study: StudyConfig,
    statistics: StatisticalConfig,
    limits: ResearchResourceLimits,
) -> EdgeResult:
    """Evaluate compression/z-score fade mean reversion on declared split data.

    Args:
        data: Source OHLC frame used for identity validation.
        split: Declared chronological split.
        study: Closed study settings.
        statistics: Seeded statistical policy.
        limits: Approved resource ceilings.

    Returns:
        Advisory mean-reversion edge result with matched null evidence.

    Raises:
        ValueError: If settings, data, or resources are invalid/insufficient.
    """
    logger.info("Running Research mean-reversion edge study")
    _enforce_rows(data, limits, "MEAN_REVERSION_ROW_LIMIT_EXCEEDED")
    settings = study.mean_reversion
    lookback = _int_setting(settings, "lookback", "MEAN_REVERSION_LOOKBACK_REQUIRED")
    entry_zscore = _float_setting(
        settings, "entry_zscore", "MEAN_REVERSION_ENTRY_ZSCORE_REQUIRED"
    )
    hold_bars = _int_setting(settings, "hold_bars", "MEAN_REVERSION_HOLD_BARS_REQUIRED")
    side = _side_setting(settings, "MEAN_REVERSION_SIDE_REQUIRED")
    minimum_samples = _int_setting(
        settings, "minimum_samples", "MEAN_REVERSION_MINIMUM_SAMPLES_REQUIRED"
    )
    q = _unit_interval_setting(settings, "q", "MEAN_REVERSION_Q_REQUIRED")
    null_quantile = _unit_interval_setting(
        settings, "null_quantile", "MEAN_REVERSION_NULL_QUANTILE_REQUIRED"
    )
    sample = split.test if "close" in split.test else data
    if "close" not in sample:
        raise ValueError("RES_INPUT_INVALID", "OHLC_COLUMNS_REQUIRED")
    close = sample["close"].astype("float64")
    rolling = close.rolling(lookback)
    zscores = (close - rolling.mean()) / rolling.std(ddof=0)
    entries = _mean_reversion_entries(zscores, side, entry_zscore)
    forward = forward_returns(close, horizon=hold_bars, mode="log", output_label="mr_f")
    observed_values = forward[entries].dropna().to_numpy(dtype="float64")
    if observed_values.size < minimum_samples:
        return _insufficient(
            "mean_reversion",
            statistics.seed,
            {
                "required_samples": minimum_samples,
                "observed_samples": int(observed_values.size),
            },
            settings,
        )
    observed = float(observed_values.mean())
    distribution = random_entry_null(
        sample,
        side=cast("Literal['buy', 'sell', 'mixed']", side),
        hold_bars=hold_bars,
        config=statistics,
    )
    return _build_edge(
        "mean_reversion",
        observed,
        distribution,
        side,
        q,
        null_quantile,
        statistics.seed,
        {"lookback": lookback, "entry_zscore": entry_zscore, "hold_bars": hold_bars},
    )


def run_eds_trend_persistence(
    data: pd.DataFrame,
    *,
    split: TimeSplitResult,
    study: StudyConfig,
    statistics: StatisticalConfig,
    limits: ResearchResourceLimits,
) -> EdgeResult:
    """Evaluate high-volatility breakout follow-through on declared split data.

    Args:
        data: Source OHLC frame used for identity validation.
        split: Declared chronological split.
        study: Closed study settings.
        statistics: Seeded statistical policy.
        limits: Approved resource ceilings.

    Returns:
        Advisory trend-persistence edge result with matched null evidence.

    Raises:
        ValueError: If settings, data, or resources are invalid/insufficient.
    """
    logger.info("Running Research trend-persistence edge study")
    _enforce_rows(data, limits, "TREND_ROW_LIMIT_EXCEEDED")
    settings = study.trend_persistence
    lookback = _int_setting(settings, "lookback", "TREND_LOOKBACK_REQUIRED")
    minimum_move = _float_setting(
        settings, "minimum_move", "TREND_MINIMUM_MOVE_REQUIRED"
    )
    hold_bars = _int_setting(settings, "hold_bars", "TREND_HOLD_BARS_REQUIRED")
    side = _side_setting(settings, "TREND_SIDE_REQUIRED")
    minimum_samples = _int_setting(
        settings, "minimum_samples", "TREND_MINIMUM_SAMPLES_REQUIRED"
    )
    q = _unit_interval_setting(settings, "q", "TREND_Q_REQUIRED")
    null_quantile = _unit_interval_setting(
        settings, "null_quantile", "TREND_NULL_QUANTILE_REQUIRED"
    )
    sample = split.test if "close" in split.test else data
    if "close" not in sample:
        raise ValueError("RES_INPUT_INVALID", "OHLC_COLUMNS_REQUIRED")
    close = sample["close"].astype("float64")
    entries = _trend_breakout_entries(close, lookback, minimum_move, side)
    forward = forward_returns(close, horizon=hold_bars, mode="log", output_label="tp_f")
    observed_values = forward[entries].dropna().to_numpy(dtype="float64")
    if observed_values.size < minimum_samples:
        return _insufficient(
            "trend_persistence",
            statistics.seed,
            {
                "required_samples": minimum_samples,
                "observed_samples": int(observed_values.size),
            },
            settings,
        )
    observed = float(observed_values.mean())
    distribution = random_entry_null(
        sample,
        side=cast("Literal['buy', 'sell', 'mixed']", side),
        hold_bars=hold_bars,
        config=statistics,
    )
    return _build_edge(
        "trend_persistence",
        observed,
        distribution,
        side,
        q,
        null_quantile,
        statistics.seed,
        {
            "lookback": lookback,
            "minimum_move": minimum_move,
            "hold_bars": hold_bars,
        },
    )


def run_eds_session(
    tagged_data: pd.DataFrame,
    *,
    split: TimeSplitResult,
    study: StudyConfig,
    statistics: StatisticalConfig,
    limits: ResearchResourceLimits,
) -> EdgeResult:
    """Evaluate breakout/fade hypotheses on a session-tagged frame with FDR.

    The frame must already carry a ``session`` column produced by
    ``seasonality.tag_sessions``; this study never redefines session windows.

    Args:
        tagged_data: OHLC frame carrying a canonical ``session`` column.
        split: Declared chronological split.
        study: Closed study settings.
        statistics: Seeded statistical policy.
        limits: Approved resource ceilings.

    Returns:
        Advisory session edge result with FDR-adjusted per-session evidence.

    Raises:
        ValueError: If session tags, settings, data, or resources are invalid.
    """
    logger.info("Running Research session edge study")
    _enforce_rows(tagged_data, limits, "SESSION_ROW_LIMIT_EXCEEDED")
    settings = study.session
    horizon = _int_setting(settings, "horizon", "SESSION_HORIZON_REQUIRED")
    minimum_samples = _int_setting(
        settings, "minimum_samples", "SESSION_MINIMUM_SAMPLES_REQUIRED"
    )
    q = _unit_interval_setting(settings, "q", "SESSION_Q_REQUIRED")
    null_quantile = _unit_interval_setting(
        settings, "null_quantile", "SESSION_NULL_QUANTILE_REQUIRED"
    )
    if "close" not in tagged_data or "session" not in tagged_data:
        raise ValueError("RES_INPUT_INVALID", "SESSION_TAGS_REQUIRED")
    sample = tagged_data.loc[split.test.index] if not split.test.empty else tagged_data
    sample = sample.dropna(subset=["close", "session"])
    close = sample["close"].astype("float64")
    forward = forward_returns(close, horizon=horizon, mode="log", output_label="ses_f")
    session_labels = sample["session"].astype("str")
    per_session: list[tuple[str, int, float, float]] = []
    p_values: list[float] = []
    rng = np.random.default_rng(statistics.seed)
    for label in sorted(set(session_labels.to_numpy())):
        mask = session_labels == label
        values = forward[mask].dropna().to_numpy(dtype="float64")
        if values.size < minimum_samples:
            continue
        observed = float(values.mean())
        null = _seeded_mean_null(values, statistics.null_samples, rng)
        p_value = float((np.sum(null >= observed) + 1) / (null.size + 1))
        per_session.append((label, int(values.size), observed, p_value))
        p_values.append(p_value)
    if not per_session:
        return _insufficient(
            "session",
            statistics.seed,
            {"required_samples": minimum_samples},
            settings,
        )
    adjusted = (
        benjamini_hochberg(p_values, q=q).tolist() if len(p_values) > 1 else p_values
    )
    classification = (
        "confirmed" if any(adj <= q for adj in adjusted) else "inconclusive"
    )
    sessions_evidence: list[JSONValue] = [
        {
            "session": name,
            "sample_size": count,
            "mean_forward_return": mean,
            "p_value": pval,
            "adjusted_p_value": adj,
        }
        for (name, count, mean, pval), adj in zip(per_session, adjusted, strict=True)
    ]
    return EdgeResult(
        "v1",
        "session",
        {
            "horizon": horizon,
            "q": q,
            "null_quantile": null_quantile,
            "session_count": len(per_session),
        },
        {
            "sessions": sessions_evidence,
            "correction": "benjamini_hochberg",
            "policy_version": "v1",
        },
        classification,
        statistics.seed,
        (),
        True,
    )


def _seeded_mean_null(
    values: np.ndarray, null_samples: int, rng: np.random.Generator
) -> np.ndarray:
    """Build a seeded resampled mean null for one session's outcomes.

    Args:
        values: Finite observed forward outcomes.
        null_samples: Requested null sample count.
        rng: Seeded generator.

    Returns:
        Seeded null distribution of resampled means.
    """
    pool = values[np.isfinite(values)]
    if pool.size == 0:
        return np.zeros(1, dtype="float64")
    output = np.empty(null_samples, dtype="float64")
    for index in range(null_samples):
        output[index] = float(rng.choice(pool, size=pool.size, replace=True).mean())
    return output


def _build_edge(
    study_name: str,
    observed: float,
    distribution: np.ndarray,
    side: Literal["buy", "sell"],
    q: float,
    null_quantile: float,
    seed: int,
    rule_config: Mapping[str, JSONValue],
) -> EdgeResult:
    """Assemble one confirmed/inconclusive advisory edge result.

    Args:
        study_name: Canonical study identifier.
        observed: Finite observed mean statistic.
        distribution: Finite matched null distribution.
        side: Declared study side.
        q: FDR control level.
        null_quantile: Null exceedance quantile.
        seed: Effective study seed.
        rule_config: Documented rule parameters.

    Returns:
        Validated advisory ``EdgeResult``.
    """
    classification = _classify(observed, distribution, side, null_quantile)
    percentile = compute_null_percentile(observed, distribution)
    return EdgeResult(
        "v1",
        study_name,
        {
            "mean": observed,
            "sample_direction": side,
            "percentile": percentile,
            "q": q,
            **rule_config,
        },
        {
            "method": "random_entry_log_return",
            "side": side,
            "distribution": distribution.tolist(),
            "summary": dict(null_distribution_stats(distribution)),
            "policy_version": "v1",
        },
        classification,
        seed,
        (),
        True,
    )


def _insufficient(
    study_name: str,
    seed: int,
    evidence: Mapping[str, JSONValue],
    settings: Mapping[str, JSONValue],
) -> EdgeResult:
    """Build an inconclusive result recording documented insufficiency.

    Args:
        study_name: Canonical study identifier.
        seed: Effective study seed.
        evidence: Insufficiency evidence.
        settings: Documented study settings.

    Returns:
        Advisory inconclusive ``EdgeResult`` with a recorded warning.
    """
    warning = ResearchWarning(
        "INSUFFICIENT_SAMPLES",
        "Edge study did not reach the declared minimum sample count",
        "warning",
        study_name,
        dict(evidence),
    )
    return EdgeResult(
        "v1",
        study_name,
        {"settings": dict(settings), **evidence},
        {"policy_version": "v1"},
        "inconclusive",
        seed,
        (warning,),
        True,
    )


__all__ = (
    "run_eds_mean_reversion",
    "run_eds_session",
    "run_eds_trend_persistence",
)
