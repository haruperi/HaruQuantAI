# ruff: noqa: PD011
"""ADX/DMI trend regime classifier.

Implements spec ``IND-RG-01`` by classifying the canonical ``trend.adx``
public wrapper's already-computed ``ADX``/``+DI``/``-DI`` trio (the one
approved cross-module dependency). This file never recalculates ADX/DMI.
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
from app.services.indicators.trend.directional import adx as _adx

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
# 0=RANGE, 1=TREND_UP, 2=TREND_DOWN, 3=TRANSITION
_RANGE, _TREND_UP, _TREND_DOWN, _TRANSITION = 0.0, 1.0, 2.0, 3.0


def _build_config(
    period: int,
    adx_trend: float,
    adx_range: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable ADX/DMI regime configuration.

    Args:
        period: The period value.
        adx_trend: The adx trend value.
        adx_range: The adx range value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="adx_dmi_regime",
        parameters=(
            ("adx_range", adx_range),
            ("adx_trend", adx_trend),
            ("period", period),
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
            "supplied config disagrees with adx_dmi_regime wrapper arguments",
            {"indicator_id": "adx_dmi_regime"},
        )
    return config


@guard_public_boundary
def adx_dmi_regime(
    data: MarketDataset,
    *,
    period: int,
    adx_trend: float,
    adx_range: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Classify spec ``IND-RG-01`` ADX/DMI trend regime.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required smoothing period fed to the canonical ADX.
        adx_trend: Required ADX trend threshold; must exceed ``adx_range``.
        adx_range: Required ADX range threshold.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ADX/DMI regime ``IndicatorResult`` carrying the
        regime candidate code (``0``=RANGE, ``1``=TREND_UP,
        ``2``=TREND_DOWN, ``3``=TRANSITION), trend strength (the ADX
        value), and signed direction.

    Raises:
        IndicatorError: If ``adx_range >= adx_trend``, or on validation or
            atomic calculation failure.
    """
    if adx_range >= adx_trend:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "adx_dmi_regime requires adx_range strictly below adx_trend",
            {"indicator_id": "adx_dmi_regime"},
        )
    logger.info("Calculating adx_dmi_regime for %s (period=%d)", data.symbol, period)
    resolved_config = _build_config(period, adx_trend, adx_range, config)
    _unwrap_indicator_response(
        validate_indicator("adx_dmi_regime", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )

    adx_result: IndicatorResult = _unwrap_indicator_response(_adx(data, period=period))
    adx_values = adx_result.values[f"adx_{period}"].to_numpy("float64")
    plus_di = adx_result.values[f"plus_di_{period}"].to_numpy("float64")
    minus_di = adx_result.values[f"minus_di_{period}"].to_numpy("float64")
    is_valid = np.isfinite(adx_values) & np.isfinite(plus_di) & np.isfinite(minus_di)

    regime_candidate = np.select(
        [
            (adx_values >= adx_trend) & (plus_di > minus_di),
            (adx_values >= adx_trend) & (minus_di > plus_di),
            adx_values <= adx_range,
        ],
        [_TREND_UP, _TREND_DOWN, _RANGE],
        default=_TRANSITION,
    )
    direction = np.sign(plus_di - minus_di)

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

    output_columns = (
        f"regime_candidate_{period}",
        f"trend_strength_{period}",
        f"regime_direction_{period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, regime_candidate, np.nan),
            output_columns[1]: np.where(is_valid, adx_values, np.nan),
            output_columns[2]: np.where(is_valid, direction, np.nan),
        },
        index=index,
    )

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=output_columns,
        output_values=output_values,
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["adx_dmi_regime"]
