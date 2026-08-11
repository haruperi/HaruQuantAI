# ruff: noqa: PD011, PLR2004
"""Final regime resolver.

Implements spec ``IND-RG-06`` by composing the four other ``regime/``
classifiers this domain publishes: ``adx_dmi_regime`` (``IND-RG-01``),
``choppiness_regime`` (``IND-RG-02``), ``donchian_breakout_regime``
(``IND-RG-04``), and ``volatility_liquidity_stress_regime``
(``IND-RG-05``, reduced-input variant). ``hurst_regime`` (``IND-RG-03``) is
intentionally excluded from the priority chain: the spec's default
priority list has no Hurst-persistence rung, so it remains a standalone
informational classifier. ``EVENT`` and ``DATA_DEGRADED`` never appear in
this domain's priority chain either, because no scheduled-event calendar
or quote-freshness input exists in the current ``MarketDataset`` contract
(see ``volatility_liquidity_stress_regime``'s module docstring); a row
where any mandatory sub-classifier is unavailable is a warmup row on this
resolver too, rather than a fabricated primary regime.
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
from app.services.indicators.regime.adx_dmi_regime import (
    adx_dmi_regime as _adx_dmi_regime,
)
from app.services.indicators.regime.choppiness_regime import (
    choppiness_regime as _choppiness_regime,
)
from app.services.indicators.regime.donchian_breakout_regime import (
    donchian_breakout_regime as _donchian_breakout_regime,
)
from app.services.indicators.regime.volatility_liquidity_stress_regime import (
    volatility_liquidity_stress_regime as _volatility_liquidity_stress_regime,
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
# 1=TRANSITION, 2=RANGE, 3=CHOPPY_RANGE, 4=TREND_UP, 5=TREND_DOWN,
# 6=BREAKOUT_UP, 7=BREAKOUT_DOWN, 8=LOW_LIQUIDITY, 9=UNSTABLE
(
    _TRANSITION,
    _RANGE,
    _CHOPPY_RANGE,
    _TREND_UP,
    _TREND_DOWN,
    _BREAKOUT_UP,
    _BREAKOUT_DOWN,
    _LOW_LIQUIDITY,
    _UNSTABLE,
) = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0)


def _build_config(
    parameters: tuple[tuple[str, int | float], ...], config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable final-regime-resolver configuration.

    Args:
        parameters: The parameters value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="final_regime_resolver",
        parameters=parameters,
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
            "supplied config disagrees with final_regime_resolver arguments",
            {"indicator_id": "final_regime_resolver"},
        )
    return config


@guard_public_boundary
def final_regime_resolver(
    data: MarketDataset,
    *,
    adx_period: int,
    adx_trend: float,
    adx_range: float,
    chop_period: int,
    chop_lower_threshold: float,
    chop_upper_threshold: float,
    donchian_period: int,
    atr_period: int,
    beta_atr: float,
    vol_reference_period: int,
    vol_period: int,
    amihud_window: int,
    p_vol_extreme: float,
    p_illiquidity_extreme: float,
    p_illiquidity_high: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Resolve spec ``IND-RG-06`` final regime from the four sub-classifiers.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        adx_period: Smoothing period fed to ``adx_dmi_regime``.
        adx_trend: Trend threshold fed to ``adx_dmi_regime``.
        adx_range: Range threshold fed to ``adx_dmi_regime``.
        chop_period: Window fed to ``choppiness_regime``.
        chop_lower_threshold: Directional threshold fed to
            ``choppiness_regime``.
        chop_upper_threshold: Choppy-range threshold fed to
            ``choppiness_regime``.
        donchian_period: Window fed to ``donchian_breakout_regime``.
        atr_period: ATR period fed to ``donchian_breakout_regime``.
        beta_atr: Breakout buffer fed to ``donchian_breakout_regime``.
        vol_reference_period: Reference window fed to
            ``volatility_liquidity_stress_regime``.
        vol_period: Volatility window fed to
            ``volatility_liquidity_stress_regime``.
        amihud_window: Amihud window fed to
            ``volatility_liquidity_stress_regime``.
        p_vol_extreme: Volatility-stress threshold fed to
            ``volatility_liquidity_stress_regime``.
        p_illiquidity_extreme: Illiquidity-stress threshold fed to
            ``volatility_liquidity_stress_regime``.
        p_illiquidity_high: Low-liquidity threshold fed to
            ``volatility_liquidity_stress_regime``.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic final-regime ``IndicatorResult`` carrying
        ``primary_regime`` (see the module-level numeric code mapping) and
        a simple ``[0, 1]`` confidence.

    Raises:
        IndicatorError: On validation or atomic calculation failure, or a
            sub-classifier configuration failure.
    """
    logger.info("Calculating final_regime_resolver for %s", data.symbol)
    parameters: tuple[tuple[str, int | float], ...] = tuple(
        sorted(
            {
                "adx_period": adx_period,
                "adx_range": adx_range,
                "adx_trend": adx_trend,
                "amihud_window": amihud_window,
                "atr_period": atr_period,
                "beta_atr": beta_atr,
                "chop_lower_threshold": chop_lower_threshold,
                "chop_period": chop_period,
                "chop_upper_threshold": chop_upper_threshold,
                "donchian_period": donchian_period,
                "p_illiquidity_extreme": p_illiquidity_extreme,
                "p_illiquidity_high": p_illiquidity_high,
                "p_vol_extreme": p_vol_extreme,
                "vol_period": vol_period,
                "vol_reference_period": vol_reference_period,
            }.items()
        )
    )
    resolved_config = _build_config(parameters, config)
    _unwrap_indicator_response(
        validate_indicator("final_regime_resolver", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )

    adx_regime: IndicatorResult = _unwrap_indicator_response(
        _adx_dmi_regime(
            data, period=adx_period, adx_trend=adx_trend, adx_range=adx_range
        )
    )
    trend_state = adx_regime.values[f"regime_candidate_{adx_period}"].to_numpy(
        "float64"
    )

    chop_regime: IndicatorResult = _unwrap_indicator_response(
        _choppiness_regime(
            data,
            period=chop_period,
            lower_threshold=chop_lower_threshold,
            upper_threshold=chop_upper_threshold,
        )
    )
    chop_state = chop_regime.values[f"choppiness_state_{chop_period}"].to_numpy(
        "float64"
    )

    breakout_regime: IndicatorResult = _unwrap_indicator_response(
        _donchian_breakout_regime(
            data, period=donchian_period, atr_period=atr_period, beta_atr=beta_atr
        )
    )
    breakout_state = breakout_regime.values[
        f"breakout_state_{donchian_period}_{atr_period}"
    ].to_numpy("float64")

    stress_regime: IndicatorResult = _unwrap_indicator_response(
        _volatility_liquidity_stress_regime(
            data,
            vol_reference_period=vol_reference_period,
            vol_period=vol_period,
            amihud_window=amihud_window,
            p_vol_extreme=p_vol_extreme,
            p_illiquidity_extreme=p_illiquidity_extreme,
            p_illiquidity_high=p_illiquidity_high,
        )
    )
    stress_suffix = f"{vol_reference_period}_{vol_period}_{amihud_window}"
    stress_state = stress_regime.values[f"stress_regime_{stress_suffix}"].to_numpy(
        "float64"
    )

    is_valid = (
        np.isfinite(trend_state)
        & np.isfinite(chop_state)
        & np.isfinite(breakout_state)
        & np.isfinite(stress_state)
    )

    # regime_candidate codes: adx_dmi_regime uses 0=RANGE,1=TREND_UP,2=TREND_DOWN,
    # 3=TRANSITION; choppiness_regime uses 0=DIRECTIONAL,1=TRANSITION,2=CHOPPY_RANGE;
    # donchian_breakout_regime uses 0=INSIDE_CHANNEL,1=BREAKOUT_UP,2=BREAKOUT_DOWN;
    # volatility_liquidity_stress_regime uses 0=NORMAL_CONDITIONS,1=LOW_LIQUIDITY,
    # 2=UNSTABLE.
    is_unstable = stress_state == 2.0
    is_low_liquidity = stress_state == 1.0
    is_breakout_up = breakout_state == 1.0
    is_breakout_down = breakout_state == 2.0
    is_trend_up = trend_state == 1.0
    is_trend_down = trend_state == 2.0
    is_choppy = chop_state == 2.0
    is_range = trend_state == 0.0

    primary_regime = np.select(
        [
            is_unstable,
            is_low_liquidity,
            is_breakout_up,
            is_breakout_down,
            is_trend_up,
            is_trend_down,
            is_choppy,
            is_range,
        ],
        [
            _UNSTABLE,
            _LOW_LIQUIDITY,
            _BREAKOUT_UP,
            _BREAKOUT_DOWN,
            _TREND_UP,
            _TREND_DOWN,
            _CHOPPY_RANGE,
            _RANGE,
        ],
        default=_TRANSITION,
    )
    confidence = np.where(primary_regime == _TRANSITION, 0.5, 1.0)

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

    output_columns = ("primary_regime", "primary_regime_confidence")
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, primary_regime, np.nan),
            output_columns[1]: np.where(is_valid, confidence, np.nan),
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


__all__ = ["final_regime_resolver"]
