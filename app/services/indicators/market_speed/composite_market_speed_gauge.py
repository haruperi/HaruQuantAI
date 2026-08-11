# ruff: noqa: PD011, PLR0915
"""Composite Market Speed gauge calculator.

Implements spec ``IND-MS-07`` by combining the canonical
``price_velocity`` (``IND-MS-01``), ``momentum_acceleration``
(``IND-MS-02``), ``volume_acceleration`` (``IND-MS-03``), and
``volatility_expansion_rate`` (``IND-MS-06``) public wrappers of this same
module/domain. ``order_flow_velocity`` (``IND-MS-05``) is intentionally
excluded from the weighted sum because its own source, OFI (``IND-OF-01``),
is unavailable in this domain (see ``order_flow/__init__.py``); the
direction/intensity formula below therefore only ever sums the four
components this domain can actually produce. Weights are supplied by the
caller (no hardcoded profile weights), and must sum to one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator
from app.services.indicators.market_speed.momentum_acceleration import (
    momentum_acceleration as _momentum_acceleration,
)
from app.services.indicators.market_speed.price_velocity import (
    price_velocity as _price_velocity,
)
from app.services.indicators.market_speed.volatility_expansion_rate import (
    volatility_expansion_rate as _volatility_expansion_rate,
)
from app.services.indicators.market_speed.volume_acceleration import (
    volume_acceleration as _volume_acceleration,
)
from app.utils import get_logger

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
_WEIGHT_TOLERANCE = 1e-6
# 0=SLOW, 1=NORMAL, 2=FAST, 3=EXTREME per the spec's default cockpit bands.
_BAND_THRESHOLDS = (25.0, 50.0, 75.0)


def _build_config(
    *,
    k: int,
    unit_seconds: float,
    volume_window: int,
    atr_period: int,
    z_window: int,
    z_max: float,
    weight_price_velocity: float,
    weight_momentum_acceleration: float,
    weight_volume_acceleration: float,
    weight_volatility_expansion: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable composite-gauge configuration.

    Args:
        k: The k value.
        unit_seconds: The unit seconds value.
        volume_window: The volume window value.
        atr_period: The atr period value.
        z_window: The z window value.
        z_max: The z max value.
        weight_price_velocity: The weight price velocity value.
        weight_momentum_acceleration: The weight momentum acceleration value.
        weight_volume_acceleration: The weight volume acceleration value.
        weight_volatility_expansion: The weight volatility expansion value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="composite_market_speed_gauge",
        parameters=(
            ("atr_period", atr_period),
            ("k", k),
            ("unit_seconds", unit_seconds),
            ("volume_window", volume_window),
            ("weight_momentum_acceleration", weight_momentum_acceleration),
            ("weight_price_velocity", weight_price_velocity),
            ("weight_volatility_expansion", weight_volatility_expansion),
            ("weight_volume_acceleration", weight_volume_acceleration),
            ("z_max", z_max),
            ("z_window", z_window),
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
            "supplied config disagrees with composite_market_speed_gauge arguments",
            {"indicator_id": "composite_market_speed_gauge"},
        )
    return config


def _rolling_z_score(values: np.ndarray, window: int) -> np.ndarray:
    """Compute a rolling z-score over a numeric array, NaN where undefined.

    Args:
        values: The values value.
        window: The window value.

    Returns:
        The np.ndarray result.

    Raises:
        None.
    """
    series = pd.Series(values)
    mean = series.rolling(window=window, min_periods=window).mean()
    std = series.rolling(window=window, min_periods=window).std(ddof=0)
    safe_std = std.where(std > 0.0)
    return np.asarray(((series - mean) / safe_std).to_numpy(dtype="float64"))


@guard_public_boundary
def composite_market_speed_gauge(
    data: MarketDataset,
    *,
    k: int,
    unit_seconds: float,
    volume_window: int,
    atr_period: int,
    z_window: int,
    z_max: float,
    weight_price_velocity: float,
    weight_momentum_acceleration: float,
    weight_volume_acceleration: float,
    weight_volatility_expansion: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate spec ``IND-MS-07`` composite market speed gauge.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        k: Shared lag fed to price velocity, momentum acceleration, volume
            acceleration, and volatility expansion rate.
        unit_seconds: Shared positive output time-unit denominator.
        volume_window: Rolling activity-volume aggregation window.
        atr_period: Smoothing period fed to the canonical ATR.
        z_window: Rolling normalization window for each component z-score.
        z_max: Positive z-score clipping bound.
        weight_price_velocity: Non-negative composite weight.
        weight_momentum_acceleration: Non-negative composite weight.
        weight_volume_acceleration: Non-negative composite weight.
        weight_volatility_expansion: Non-negative composite weight.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic composite-gauge ``IndicatorResult`` carrying
        ``composite_score`` in ``[0, 100]``, ``speed_band``
        (``0``=SLOW, ``1``=NORMAL, ``2``=FAST, ``3``=EXTREME), signed
        ``direction``, and the four per-component contributions.

    Raises:
        IndicatorError: If the supplied weights do not sum to one, or on
            validation/atomic calculation failure.
    """
    weights = (
        weight_price_velocity,
        weight_momentum_acceleration,
        weight_volume_acceleration,
        weight_volatility_expansion,
    )
    if any(weight < 0.0 for weight in weights) or abs(sum(weights) - 1.0) > (
        _WEIGHT_TOLERANCE
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "composite_market_speed_gauge weights must be non-negative and sum to one",
            {"indicator_id": "composite_market_speed_gauge"},
        )
    logger.info("Calculating composite_market_speed_gauge for %s", data.symbol)
    resolved_config = _build_config(
        k=k,
        unit_seconds=unit_seconds,
        volume_window=volume_window,
        atr_period=atr_period,
        z_window=z_window,
        z_max=z_max,
        weight_price_velocity=weight_price_velocity,
        weight_momentum_acceleration=weight_momentum_acceleration,
        weight_volume_acceleration=weight_volume_acceleration,
        weight_volatility_expansion=weight_volatility_expansion,
        config=config,
    )
    _unwrap_indicator_response(
        validate_indicator("composite_market_speed_gauge", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    pv_result: IndicatorResult = _unwrap_indicator_response(
        _price_velocity(data, k=k, unit_seconds=unit_seconds)
    )
    pa_result: IndicatorResult = _unwrap_indicator_response(
        _momentum_acceleration(data, k=k, unit_seconds=unit_seconds)
    )
    va_result: IndicatorResult = _unwrap_indicator_response(
        _volume_acceleration(data, window=volume_window, k=k, unit_seconds=unit_seconds)
    )
    ver_result: IndicatorResult = _unwrap_indicator_response(
        _volatility_expansion_rate(
            data, atr_period=atr_period, k=k, unit_seconds=unit_seconds
        )
    )

    pv = pv_result.values[f"price_velocity_{k}"].to_numpy("float64")
    pa = pa_result.values[f"price_acceleration_{k}"].to_numpy("float64")
    va = va_result.values[f"volume_acceleration_{volume_window}_{k}"].to_numpy(
        "float64"
    )
    ver = ver_result.values[f"volatility_expansion_rate_{atr_period}_{k}"].to_numpy(
        "float64"
    )

    z_pv = _rolling_z_score(pv, z_window)
    z_pa = _rolling_z_score(pa, z_window)
    z_va = _rolling_z_score(va, z_window)
    z_ver = _rolling_z_score(ver, z_window)

    def _unit_contribution(z: np.ndarray) -> np.ndarray:
        """Normalize one clipped z-score contribution.

        Args:
            z: Rolling z-score values.

        Returns:
            The bounded absolute contribution array.

        Raises:
            None.
        """
        clipped = np.clip(z, -z_max, z_max)
        return np.asarray(np.abs(clipped) / z_max)

    u_pv = _unit_contribution(z_pv)
    u_pa = _unit_contribution(z_pa)
    u_va = _unit_contribution(z_va)
    u_ver = _unit_contribution(z_ver)

    is_valid = (
        np.isfinite(z_pv) & np.isfinite(z_pa) & np.isfinite(z_va) & np.isfinite(z_ver)
    )

    contribution_pv = weight_price_velocity * u_pv
    contribution_pa = weight_momentum_acceleration * u_pa
    contribution_va = weight_volume_acceleration * u_va
    contribution_ver = weight_volatility_expansion * u_ver
    composite_score = 100.0 * (
        contribution_pv + contribution_pa + contribution_va + contribution_ver
    )

    speed_band = np.select(
        [
            composite_score < _BAND_THRESHOLDS[0],
            composite_score < _BAND_THRESHOLDS[1],
            composite_score < _BAND_THRESHOLDS[2],
        ],
        [0.0, 1.0, 2.0],
        default=3.0,
    )
    direction = np.sign(z_pv + z_pa)
    direction = np.where(np.isfinite(direction), direction, 0.0)

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

    suffix = f"{k}_{volume_window}_{atr_period}_{z_window}"
    output_columns = (
        f"composite_score_{suffix}",
        f"speed_band_{suffix}",
        f"speed_direction_{suffix}",
        f"speed_contribution_price_velocity_{suffix}",
        f"speed_contribution_momentum_acceleration_{suffix}",
        f"speed_contribution_volume_acceleration_{suffix}",
        f"speed_contribution_volatility_expansion_{suffix}",
    )
    values_by_column = (
        composite_score,
        speed_band,
        direction,
        contribution_pv,
        contribution_pa,
        contribution_va,
        contribution_ver,
    )
    output_values = pd.DataFrame(
        {
            column: np.where(is_valid, series, np.nan)
            for column, series in zip(output_columns, values_by_column, strict=True)
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


__all__ = ["composite_market_speed_gauge"]
