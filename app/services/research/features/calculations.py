"""Pure Research-owned return, Hurst, and forward-outcome calculations."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from app.utils import logger
from app.utils.errors import ValidationError

_MIN_HURST_SAMPLES = 20
_MAX_HURST_LAG = 20
_MIN_RETURN_SAMPLES = 2
_MIN_REGRESSION_POINTS = 2


def _numeric_series(values: pd.Series, *, positive: bool = False) -> pd.Series:
    """Validate and detach one finite numeric series.

    Args:
        values: Candidate numeric series.
        positive: Whether values must be strictly positive.

    Returns:
        Detached float64 series.

    Raises:
        ValidationError: If values are empty, non-finite, or non-positive.
    """
    logger.debug("Validating Research numeric series")
    if not isinstance(values, pd.Series) or values.empty:
        raise ValidationError("RES_INSUFFICIENT_DATA", "NONEMPTY_SERIES_REQUIRED")
    output = values.astype("float64").copy(deep=True)
    if not np.isfinite(output.to_numpy()).all():
        raise ValidationError("RES_NONFINITE_DATA", "FINITE_SERIES_REQUIRED")
    if positive and bool((output <= 0).any()):
        raise ValidationError("RES_INPUT_INVALID", "POSITIVE_VALUES_REQUIRED")
    return output


def log_returns(close: pd.Series) -> pd.Series:
    """Compute aligned one-period log returns without mutation.

    Args:
        close: Strictly positive finite close-price series.

    Returns:
        Float64 series with a warm-up NaN in the first row.

    Raises:
        ValidationError: If input is invalid or insufficient.
    """
    logger.info("Computing Research log returns")
    values = _numeric_series(close, positive=True)
    if len(values) < _MIN_RETURN_SAMPLES:
        raise ValidationError("RES_INSUFFICIENT_DATA", "TWO_PRICES_REQUIRED")
    result = np.log(values / values.shift(1))
    result.name = "log_return"
    return result


def simple_returns(close: pd.Series) -> pd.Series:
    """Compute aligned one-period arithmetic returns without mutation.

    Args:
        close: Strictly positive finite close-price series.

    Returns:
        Float64 series with a warm-up NaN in the first row.

    Raises:
        ValidationError: If input is invalid or insufficient.
    """
    logger.info("Computing Research simple returns")
    values = _numeric_series(close, positive=True)
    if len(values) < _MIN_RETURN_SAMPLES:
        raise ValidationError("RES_INSUFFICIENT_DATA", "TWO_PRICES_REQUIRED")
    result = values.pct_change(fill_method=None)
    result.name = "simple_return"
    return result


def hurst_exponent(values: pd.Series, *, minimum_samples: int) -> float:
    """Estimate the Hurst exponent by log-log lag dispersion regression.

    Args:
        values: Finite non-constant observations.
        minimum_samples: Required finite sample, at least 20.

    Returns:
        Finite Hurst exponent estimate.

    Raises:
        ValidationError: If sample, finiteness, or variance is invalid.
    """
    logger.info("Estimating Research Hurst exponent")
    if minimum_samples < _MIN_HURST_SAMPLES:
        raise ValidationError("RES_INPUT_INVALID", "HURST_MINIMUM_BELOW_POLICY")
    sample = _numeric_series(values).dropna()
    if len(sample) < minimum_samples:
        raise ValidationError("RES_INSUFFICIENT_DATA", "HURST_SAMPLE_TOO_SMALL")
    if bool(sample.eq(sample.iloc[0]).all()):
        raise ValidationError("RES_INPUT_INVALID", "CONSTANT_HURST_SAMPLE")
    maximum_lag = min(_MAX_HURST_LAG, len(sample) // 2)
    lags = np.arange(2, maximum_lag + 1, dtype="float64")
    dispersions = np.asarray(
        [
            np.std(sample.to_numpy()[lag:] - sample.to_numpy()[:-lag])
            for lag in lags.astype(int)
        ],
        dtype="float64",
    )
    valid = dispersions > 0
    if int(valid.sum()) < _MIN_REGRESSION_POINTS:
        raise ValidationError("RES_INSUFFICIENT_DATA", "HURST_LAGS_INSUFFICIENT")
    estimate = float(np.polyfit(np.log(lags[valid]), np.log(dispersions[valid]), 1)[0])
    if not np.isfinite(estimate):
        raise ValidationError("RES_NONFINITE_DATA", "HURST_ESTIMATE_NONFINITE")
    return estimate


def rolling_hurst(values: pd.Series, *, window: int, minimum_samples: int) -> pd.Series:
    """Compute aligned rolling Hurst values with explicit warm-up NaNs.

    Args:
        values: Finite observations.
        window: Rolling window size.
        minimum_samples: Required observations in each window.

    Returns:
        Aligned float64 series.

    Raises:
        ValidationError: If window or sample policy is invalid.
    """
    logger.info("Computing rolling Research Hurst exponent")
    sample = _numeric_series(values)
    if window < minimum_samples or minimum_samples < _MIN_HURST_SAMPLES:
        raise ValidationError("RES_INPUT_INVALID", "INVALID_HURST_WINDOW")
    result = sample.rolling(window=window, min_periods=window).apply(
        lambda item: hurst_exponent(pd.Series(item), minimum_samples=minimum_samples),
        raw=False,
    )
    result.name = f"hurst_{window}"
    return result


def forward_returns(
    close: pd.Series,
    *,
    horizon: int,
    mode: Literal["log", "simple"],
    output_label: str,
) -> pd.Series:
    """Compute a horizon-aligned research-only forward return.

    Args:
        close: Strictly positive finite close prices.
        horizon: Positive forward bar count.
        mode: Logarithmic or arithmetic return convention.
        output_label: Explicit output name.

    Returns:
        Aligned series with trailing unavailable rows as NaN and research-only attrs.

    Raises:
        ValidationError: If mode, horizon, label, or data is invalid.
    """
    logger.info("Computing Research forward returns")
    values = _numeric_series(close, positive=True)
    if not 0 < horizon < len(values) or not output_label.strip():
        raise ValidationError("RES_INPUT_INVALID", "INVALID_FORWARD_RETURN_POLICY")
    ratio = values.shift(-horizon) / values
    result = np.log(ratio) if mode == "log" else ratio - 1.0
    result.name = output_label
    result.attrs["research_only"] = True
    result.attrs["horizon"] = horizon
    result.attrs["mode"] = mode
    return result


def _forward_extreme(
    data: pd.DataFrame, *, horizon: int, side: Literal["buy", "sell"], favorable: bool
) -> pd.Series:
    """Compute one direction-aware forward excursion.

    Args:
        data: Frame containing high, low, and close.
        horizon: Positive forward bar count.
        side: Buy or sell direction.
        favorable: Whether to calculate favorable rather than adverse movement.

    Returns:
        Aligned excursion series with trailing NaNs.

    Raises:
        ValidationError: If input or policy is invalid.
    """
    logger.debug("Computing direction-aware Research excursion")
    if not {"high", "low", "close"} <= set(data.columns):
        raise ValidationError("RES_INPUT_INVALID", "OHLC_COLUMNS_REQUIRED")
    if side not in {"buy", "sell"} or not 0 < horizon < len(data):
        raise ValidationError("RES_INPUT_INVALID", "INVALID_EXCURSION_POLICY")
    values = data[["high", "low", "close"]].astype("float64")
    output = pd.Series(np.nan, index=data.index, dtype="float64")
    for position in range(len(values) - horizon):
        future = values.iloc[position + 1 : position + horizon + 1]
        close = float(values["close"].iloc[position])
        if side == "buy":
            price = float(future["high"].max() if favorable else future["low"].min())
            output.iloc[position] = price / close - 1.0
        else:
            price = float(future["low"].min() if favorable else future["high"].max())
            output.iloc[position] = close / price - 1.0
    output.attrs["research_only"] = True
    output.attrs["horizon"] = horizon
    output.attrs["side"] = side
    return output


def forward_max_favorable_excursion(
    data: pd.DataFrame, *, horizon: int, side: Literal["buy", "sell"]
) -> pd.Series:
    """Compute direction-aware maximum favorable excursion.

    Args:
        data: Frame containing high, low, and close.
        horizon: Positive forward bar count.
        side: Buy or sell direction.

    Returns:
        Aligned favorable-excursion series.

    Raises:
        ValidationError: If input or policy is invalid.
    """
    logger.info("Computing Research maximum favorable excursion")
    result = _forward_extreme(data, horizon=horizon, side=side, favorable=True)
    result.name = f"forward_mfe_{side}_{horizon}"
    return result


def forward_max_adverse_excursion(
    data: pd.DataFrame, *, horizon: int, side: Literal["buy", "sell"]
) -> pd.Series:
    """Compute direction-aware maximum adverse excursion.

    Args:
        data: Frame containing high, low, and close.
        horizon: Positive forward bar count.
        side: Buy or sell direction.

    Returns:
        Aligned adverse-excursion series.

    Raises:
        ValidationError: If input or policy is invalid.
    """
    logger.info("Computing Research maximum adverse excursion")
    result = _forward_extreme(data, horizon=horizon, side=side, favorable=False)
    result.name = f"forward_mae_{side}_{horizon}"
    return result


__all__ = (
    "forward_max_adverse_excursion",
    "forward_max_favorable_excursion",
    "forward_returns",
    "hurst_exponent",
    "log_returns",
    "rolling_hurst",
    "simple_returns",
)
