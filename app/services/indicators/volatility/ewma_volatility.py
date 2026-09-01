# ruff: noqa: PLR2004
"""EWMA (RiskMetrics-style) volatility calculator.

Implements spec ``IND-VOL-04``:

``sigma_t^2 = lambda * sigma_{t-1}^2 + (1 - lambda) * r_t^2``
``sigma_t^ann = sqrt(A * sigma_t^2)``

The seed variance is declared explicitly: the first observed squared log
return seeds ``sigma^2``, so the series is valid from the first return
onward (row index 1) with no artificial extra warmup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.composition.logging import get_logger
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.contracts import (
        _OHLCVRecord as OHLCVRecord,
    )
    from app.services.indicators.core.results import IndicatorResult

_FORMULA_VERSION = "1.0.0"
_INDICATOR_VERSION = "1.0.0"
_DEFAULT_ANNUALIZATION_FACTOR = 252.0


def _build_config(
    decay: float, annualization_factor: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable EWMA volatility configuration.

    Args:
        decay: Required RiskMetrics decay ``lambda`` in ``(0, 1)``.
        annualization_factor: Declared annualization factor ``A``.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    expected = IndicatorConfig(
        indicator_id="ewma_volatility",
        parameters=(
            ("annualization_factor", annualization_factor),
            ("decay", decay),
        ),
        source=None,
        formula_version=_FORMULA_VERSION,
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    if config is None:
        return expected
    if (
        config.indicator_id != expected.indicator_id
        or config.parameters != expected.parameters
        or config.source is not None
        or config.formula_version != expected.formula_version
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with ewma_volatility wrapper arguments",
            {"indicator_id": "ewma_volatility"},
        )
    return config


def _ewma_variance(log_returns: np.ndarray, decay: float) -> np.ndarray:
    """Calculate the seeded EWMA variance series over log returns.

    Args:
            log_returns: Row-ordered consecutive log returns.
            decay: RiskMetrics decay ``lambda`` in ``(0, 1)``.

    Returns:
            A float64 variance array aligned to ``log_returns``, seeded by the
            first squared return.

    Raises:
        None.
    """
    variance = np.full(len(log_returns), np.nan, dtype="float64")
    if len(log_returns) == 0:
        return variance
    variance[0] = log_returns[0] ** 2
    for position in range(1, len(log_returns)):
        variance[position] = (
            decay * variance[position - 1] + (1.0 - decay) * log_returns[position] ** 2
        )
    return variance


@guard_public_boundary
def ewma_volatility(
    data: MarketDataset,
    *,
    decay: float,
    annualization_factor: float = _DEFAULT_ANNUALIZATION_FACTOR,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate RiskMetrics-style EWMA annualized volatility on close.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        decay: Required RiskMetrics decay ``lambda`` in ``(0, 1)``.
        annualization_factor: The declared annualization factor ``A``;
            defaults to 252 trading days but is a profile parameter, never
            a hardcoded constant.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic EWMA volatility ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating ewma_volatility for %s (decay=%s, A=%s)",
        data.symbol,
        decay,
        annualization_factor,
    )
    resolved_config = _build_config(decay, annualization_factor, config)
    _unwrap_indicator_response(
        validate_indicator("ewma_volatility", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    row_count = len(records)
    is_valid = np.zeros(row_count, dtype=bool)
    values = np.full(row_count, np.nan, dtype="float64")
    if row_count >= 2:
        log_returns = np.diff(np.log(close))
        variance = _ewma_variance(log_returns, decay)
        is_valid[1:] = True
        values[1:] = np.sqrt(annualization_factor * variance)

    computed_from_start = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_end = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    if is_valid.any():
        computed_from_start[is_valid] = records[0].timestamp
        computed_from_end[is_valid] = index[is_valid]
    available_at = pd.Series([record.available_at for record in records], index=index)
    cumulative_available = available_at.cummax()
    available_at[is_valid] = cumulative_available[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"
    output_column = "ewma_volatility"

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=(output_column,),
        output_values=pd.DataFrame({output_column: values}, index=index),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["ewma_volatility"]
