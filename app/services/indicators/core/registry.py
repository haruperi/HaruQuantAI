"""Immutable official Indicators registry and capability matrix.

Describes the sixty-four official built-in indicators and the Core-supported
execution modes. The registry stores no runtime registrations, performs no
plugin discovery, and never imports a feature implementation module.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.composition.logging import get_logger
from app.services.indicators.core.contracts import IndicatorSpec
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)

logger = get_logger(__name__)

_REGISTRY_PARAMETER_SCHEMA_MAXIMUM = 1_000_000
_WORKFLOW_ELIGIBILITY: tuple[str, ...] = (
    "WF-INDI-001",
    "WF-INDI-002",
    "WF-INDI-003",
    "WF-INDI-004",
)
_UNSUPPORTED_OPTIONAL_MODES: tuple[str, ...] = (
    "incremental",
    "streaming",
    "cache",
    "composition",
    "custom_registration",
    "out_of_core",
    "acceleration",
    "proprietary",
)
_UNSUPPORTED_CODES: Mapping[str, str] = MappingProxyType(
    dict.fromkeys(_UNSUPPORTED_OPTIONAL_MODES, "IND_INVALID_CONFIG")
)


def _period_schema(*, required: bool, default: int | None) -> Mapping[str, object]:
    """Build the frozen canonical period parameter schema entry.

    Args:
            required: Whether the period parameter is mandatory.
            default: The registry default period, or ``None`` when required.

    Returns:
            A frozen JSON-compatible period schema mapping.

    Raises:
        None.
    """
    return MappingProxyType(
        {
            "type": "integer",
            "minimum": 2,
            "maximum": _REGISTRY_PARAMETER_SCHEMA_MAXIMUM,
            "required": required,
            "default": default,
        }
    )


def _number_schema(
    *, required: bool, default: float | None, minimum: float, maximum: float
) -> Mapping[str, object]:
    """Build a frozen non-period numeric parameter schema entry.

        Generalizes ``_period_schema`` for formula-specific numeric parameters
        (for example a standard-deviation multiplier or a candlestick body
        threshold) so they can be declared and validated through the same
        generic parameter-schema engine as ``period``.

    Args:
            required: Whether the parameter is mandatory.
            default: The registry default value, or ``None`` when required.
            minimum: Inclusive lower bound.
            maximum: Inclusive upper bound.

    Returns:
            A frozen JSON-compatible numeric schema mapping.

    Raises:
        None.
    """
    return MappingProxyType(
        {
            "type": "number",
            "minimum": minimum,
            "maximum": maximum,
            "required": required,
            "default": default,
        }
    )


def _integer_schema(
    *, required: bool, default: int | None, minimum: int, maximum: int
) -> Mapping[str, object]:
    """Build a frozen non-period integer parameter schema entry.

        Generalizes ``_period_schema`` for formula-specific integer parameters
        that are not the canonical ``period`` (for example a volume-profile bin
        count).

    Args:
            required: Whether the parameter is mandatory.
            default: The registry default value, or ``None`` when required.
            minimum: Inclusive lower bound.
            maximum: Inclusive upper bound.

    Returns:
            A frozen JSON-compatible integer schema mapping.

    Raises:
        None.
    """
    return MappingProxyType(
        {
            "type": "integer",
            "minimum": minimum,
            "maximum": maximum,
            "required": required,
            "default": default,
        }
    )


def _spec(
    *,
    indicator_id: str,
    name: str,
    required_columns: tuple[str, ...],
    output_templates: tuple[str, ...],
    warmup_policy: str,
    import_path: str,
    period_required: bool = False,
    period_default: int | None = None,
    parameter_schema: Mapping[str, object] | None = None,
) -> IndicatorSpec:
    """Build one immutable official ``IndicatorSpec`` registry entry.

    Args:
            indicator_id: Stable lowercase official registry identifier.
            name: Human-readable indicator name.
            required_columns: Fixed OHLC columns or the ``"source"`` placeholder.
            output_templates: Deterministic output-name templates in order.
            warmup_policy: Declared warmup convention for the indicator.
            import_path: Stable dotted import path to the official callable.
            period_required: Whether the sole parameter is a mandatory period.
                Ignored when ``parameter_schema`` is supplied explicitly.
            period_default: The registry default period, or ``None``. Ignored
                when ``parameter_schema`` is supplied explicitly.
            parameter_schema: An explicit frozen parameter schema for
                indicators whose parameters are not exactly one ``period``
                (parameterless indicators use an empty mapping; multi-parameter
                or non-period-named indicators declare every key here).

    Returns:
            The immutable official ``IndicatorSpec``.

    Raises:
        None.
    """
    resolved_schema = (
        parameter_schema
        if parameter_schema is not None
        else {
            "period": _period_schema(required=period_required, default=period_default)
        }
    )
    return IndicatorSpec(
        indicator_id=indicator_id,
        name=name,
        indicator_version="1.0.0",
        formula_version="1.0.0",
        tier="core_mvp",
        required_columns=required_columns,
        parameter_schema=MappingProxyType(dict(resolved_schema)),
        output_templates=output_templates,
        warmup_policy=warmup_policy,  # type: ignore[arg-type]
        vectorized=True,
        multi_symbol=False,
        multi_timeframe=False,
        import_path=import_path,
        stability="stable",
        workflow_eligibility=_WORKFLOW_ELIGIBILITY,
    )


_REGISTRY: Mapping[str, IndicatorSpec] = MappingProxyType(
    {
        spec.indicator_id: spec
        for spec in (
            _spec(
                indicator_id="aggressive_trade_imbalance",
                name="Aggressive Trade Imbalance",
                required_columns=("open", "close", "volume"),
                output_templates=(
                    "aggressive_trade_imbalance_{window}",
                    "aggressive_trade_imbalance_buy_volume_{window}",
                    "aggressive_trade_imbalance_sell_volume_{window}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.order_flow."
                    "aggressive_trade_imbalance:aggressive_trade_imbalance"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "window": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="anchored_vwap",
                name="Anchored VWAP",
                required_columns=("high", "low", "close", "volume"),
                output_templates=(
                    "anchored_vwap_{anchor_index}",
                    "anchored_vwap_cumulative_volume_{anchor_index}",
                    "anchored_vwap_deviation_{anchor_index}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.structure.anchored_vwap:anchored_vwap"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "anchor_index": _integer_schema(
                            required=True, default=None, minimum=0, maximum=1_000_000
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="adx",
                name="Average Directional Index",
                required_columns=("high", "low", "close"),
                period_required=False,
                period_default=14,
                output_templates=(
                    "adx_{period}",
                    "plus_di_{period}",
                    "minus_di_{period}",
                ),
                warmup_policy="two_period",
                import_path="app.services.indicators.trend.directional:adx",
            ),
            _spec(
                indicator_id="adr",
                name="Average Daily Range",
                required_columns=("high", "low"),
                period_required=False,
                period_default=14,
                output_templates=("adr_{period}",),
                warmup_policy="period",
                import_path="app.services.indicators.volatility.adr:adr",
            ),
            _spec(
                indicator_id="atr",
                name="Average True Range",
                required_columns=("high", "low", "close"),
                period_required=False,
                period_default=14,
                output_templates=("atr_{period}", "true_range"),
                warmup_policy="period",
                import_path="app.services.indicators.volatility.atr:atr",
            ),
            _spec(
                indicator_id="atr_percent",
                name="ATR Percent",
                required_columns=("high", "low", "close"),
                period_required=False,
                period_default=14,
                output_templates=("atr_percent_{period}",),
                warmup_policy="period",
                import_path="app.services.indicators.volatility.atr_percent:atr_percent",
            ),
            _spec(
                indicator_id="bollinger_bands",
                name="Bollinger Bands",
                required_columns=("close",),
                output_templates=(
                    "bollinger_bands_upper_{period}",
                    "bollinger_bands_middle_{period}",
                    "bollinger_bands_lower_{period}",
                ),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.trend.bollinger_bands:bollinger_bands"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "period": _period_schema(required=True, default=None),
                        "std_dev": _number_schema(
                            required=True,
                            default=None,
                            minimum=1e-12,
                            maximum=1_000_000.0,
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="bollinger_bandwidth",
                name="Bollinger BandWidth",
                required_columns=("close",),
                output_templates=(
                    "bollinger_bandwidth_upper_{period}",
                    "bollinger_bandwidth_middle_{period}",
                    "bollinger_bandwidth_lower_{period}",
                    "bollinger_bandwidth_percent_{period}",
                ),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.volatility.bollinger_bandwidth:"
                    "bollinger_bandwidth"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "period": _period_schema(required=True, default=None),
                        "std_dev": _number_schema(
                            required=True,
                            default=None,
                            minimum=1e-12,
                            maximum=1_000_000.0,
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="cmf",
                name="Chaikin Money Flow",
                required_columns=("high", "low", "close", "volume"),
                output_templates=("cmf_{period}",),
                warmup_policy="period",
                import_path="app.services.indicators.volume.cmf:cmf",
                period_required=True,
                period_default=None,
            ),
            _spec(
                indicator_id="doji",
                name="Doji",
                required_columns=("open", "high", "low", "close"),
                output_templates=("doji",),
                warmup_policy="none",
                import_path="app.services.indicators.patterns.doji:doji",
                parameter_schema=MappingProxyType(
                    {
                        "threshold": _number_schema(
                            required=True,
                            default=None,
                            minimum=1e-12,
                            maximum=1.0,
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="ema",
                name="Exponential Moving Average",
                required_columns=("source",),
                period_required=True,
                period_default=None,
                output_templates=("ema_{period}", "ema_{source}_{period}"),
                warmup_policy="period",
                import_path="app.services.indicators.trend.ema:ema",
            ),
            _spec(
                indicator_id="engulfing",
                name="Engulfing",
                required_columns=("open", "close"),
                output_templates=("engulfing",),
                warmup_policy="custom",
                import_path="app.services.indicators.patterns.engulfing:engulfing",
                parameter_schema=MappingProxyType({}),
            ),
            _spec(
                indicator_id="ewma_volatility",
                name="EWMA Volatility",
                required_columns=("close",),
                output_templates=("ewma_volatility",),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.volatility.ewma_volatility:ewma_volatility"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "annualization_factor": _number_schema(
                            required=False,
                            default=252.0,
                            minimum=1e-9,
                            maximum=1_000_000.0,
                        ),
                        "decay": _number_schema(
                            required=True,
                            default=None,
                            minimum=1e-9,
                            maximum=0.999999,
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="garman_klass_volatility",
                name="Garman-Klass Volatility",
                required_columns=("open", "high", "low", "close"),
                output_templates=("garman_klass_volatility_{period}",),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.volatility.garman_klass_volatility:"
                    "garman_klass_volatility"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "annualization_factor": _number_schema(
                            required=False,
                            default=252.0,
                            minimum=1e-9,
                            maximum=1_000_000.0,
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="hull_ma",
                name="Hull Moving Average",
                required_columns=("source",),
                output_templates=("hull_ma_{period}", "hull_ma_{source}_{period}"),
                warmup_policy="custom",
                import_path="app.services.indicators.trend.hull_ma:hull_ma",
                period_required=True,
                period_default=None,
            ),
            _spec(
                indicator_id="inside_bar",
                name="Inside Bar",
                required_columns=("high", "low"),
                output_templates=("inside_bar",),
                warmup_policy="custom",
                import_path="app.services.indicators.patterns.inside_bar:inside_bar",
                parameter_schema=MappingProxyType({}),
            ),
            _spec(
                indicator_id="mfi",
                name="Money Flow Index",
                required_columns=("high", "low", "close", "volume"),
                output_templates=("mfi_{period}",),
                warmup_policy="period",
                import_path="app.services.indicators.volume.mfi:mfi",
                period_required=True,
                period_default=None,
            ),
            _spec(
                indicator_id="obv",
                name="On-Balance Volume",
                required_columns=("close", "volume"),
                output_templates=("obv",),
                warmup_policy="none",
                import_path="app.services.indicators.volume.obv:obv",
                parameter_schema=MappingProxyType({}),
            ),
            _spec(
                indicator_id="parkinson_volatility",
                name="Parkinson Range Volatility",
                required_columns=("high", "low"),
                output_templates=("parkinson_volatility_{period}",),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.volatility.parkinson_volatility:"
                    "parkinson_volatility"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "annualization_factor": _number_schema(
                            required=False,
                            default=252.0,
                            minimum=1e-9,
                            maximum=1_000_000.0,
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="pinbar",
                name="Pinbar",
                required_columns=("open", "high", "low", "close"),
                output_templates=("pinbar",),
                warmup_policy="none",
                import_path="app.services.indicators.patterns.pinbar:pinbar",
                parameter_schema=MappingProxyType({}),
            ),
            _spec(
                indicator_id="price_volume_distribution",
                name="Price Volume Distribution",
                required_columns=("high", "low", "close", "volume"),
                output_templates=("price_volume_distribution_{period}_{bins}",),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.volume.price_volume_distribution:"
                    "price_volume_distribution"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "bins": _integer_schema(
                            required=True,
                            default=None,
                            minimum=1,
                            maximum=10_000,
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="rogers_satchell_volatility",
                name="Rogers-Satchell Volatility",
                required_columns=("open", "high", "low", "close"),
                output_templates=("rogers_satchell_volatility_{period}",),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.volatility."
                    "rogers_satchell_volatility:rogers_satchell_volatility"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "annualization_factor": _number_schema(
                            required=False,
                            default=252.0,
                            minimum=1e-9,
                            maximum=1_000_000.0,
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="rolling_volatility",
                name="Rolling Volatility",
                required_columns=("source",),
                output_templates=(
                    "rolling_volatility_{period}",
                    "rolling_volatility_{source}_{period}",
                ),
                warmup_policy="period_plus_one",
                import_path=(
                    "app.services.indicators.volatility.rolling_volatility:"
                    "rolling_volatility"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "annualization_factor": _number_schema(
                            required=False,
                            default=252.0,
                            minimum=1e-9,
                            maximum=1_000_000.0,
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="rsi",
                name="Relative Strength Index",
                required_columns=("source",),
                period_required=False,
                period_default=14,
                output_templates=("rsi_{period}", "rsi_{source}_{period}"),
                warmup_policy="period_plus_one",
                import_path="app.services.indicators.momentum.rsi:rsi",
            ),
            _spec(
                indicator_id="sma",
                name="Simple Moving Average",
                required_columns=("source",),
                period_required=True,
                period_default=None,
                output_templates=("sma_{period}", "sma_{source}_{period}"),
                warmup_policy="period",
                import_path="app.services.indicators.trend.sma:sma",
            ),
            _spec(
                indicator_id="standard_deviation",
                name="Standard Deviation",
                required_columns=("source",),
                output_templates=(
                    "standard_deviation_{period}",
                    "standard_deviation_{source}_{period}",
                ),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.volatility.standard_deviation:"
                    "standard_deviation"
                ),
                period_required=True,
                period_default=None,
            ),
            _spec(
                indicator_id="volatility_of_volatility",
                name="Volatility of Volatility",
                required_columns=("close",),
                output_templates=("volatility_of_volatility_{period}_{vol_period}",),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.volatility.volatility_of_volatility:"
                    "volatility_of_volatility"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "period": _period_schema(required=True, default=None),
                        "vol_period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="volatility_percentile",
                name="Volatility Percentile and Z-Score",
                required_columns=("close",),
                output_templates=(
                    "volatility_percentile_{reference_period}_{vol_period}",
                    "volatility_zscore_{reference_period}_{vol_period}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.volatility.volatility_percentile:"
                    "volatility_percentile"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "annualization_factor": _number_schema(
                            required=False,
                            default=252.0,
                            minimum=1e-9,
                            maximum=1_000_000.0,
                        ),
                        "reference_period": _period_schema(required=True, default=None),
                        "vol_period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="williams_r",
                name="Williams %R",
                required_columns=("high", "low", "close"),
                period_required=False,
                period_default=14,
                output_templates=("williams_r_{period}",),
                warmup_policy="period",
                import_path="app.services.indicators.momentum.williams_r:williams_r",
            ),
            _spec(
                indicator_id="wma",
                name="Weighted Moving Average",
                required_columns=("source",),
                output_templates=("wma_{period}", "wma_{source}_{period}"),
                warmup_policy="period",
                import_path="app.services.indicators.trend.wma:wma",
                period_required=True,
                period_default=None,
            ),
            _spec(
                indicator_id="zigzag",
                name="Causal Confirmed ZigZag",
                required_columns=("high", "low"),
                output_templates=(
                    "zigzag_value_{depth}",
                    "zigzag_type_{depth}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.trend.zigzag:zigzag",
                parameter_schema=MappingProxyType(
                    {
                        "depth": _integer_schema(
                            required=True,
                            default=None,
                            minimum=2,
                            maximum=10_000,
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="aroon",
                name="Aroon Up/Down/Oscillator",
                required_columns=("high", "low"),
                output_templates=(
                    "aroon_up_{lookback}",
                    "aroon_down_{lookback}",
                    "aroon_oscillator_{lookback}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.trend.aroon:aroon",
                parameter_schema=MappingProxyType(
                    {
                        "lookback": _integer_schema(
                            required=True, default=None, minimum=1, maximum=10_000
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="ema_slope",
                name="EMA and ATR-Normalized EMA Slope",
                required_columns=("close", "high", "low"),
                output_templates=(
                    "ema_slope_ema_{period}",
                    "ema_slope_raw_{period}_{lag}",
                    "ema_slope_normalized_{period}_{lag}_{atr_period}",
                    "ema_slope_direction_{period}_{lag}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.trend.ema_slope:ema_slope",
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "lag": _integer_schema(
                            required=True, default=None, minimum=1, maximum=10_000
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="linear_regression_trend",
                name="Linear-Regression Slope and Trend Fit",
                required_columns=("close",),
                output_templates=(
                    "linear_regression_slope_{period}_{transform}",
                    "linear_regression_intercept_{period}_{transform}",
                    "linear_regression_r_squared_{period}_{transform}",
                    "linear_regression_fitted_end_{period}_{transform}",
                    "linear_regression_direction_{period}_{transform}",
                ),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.trend.linear_regression_trend:"
                    "linear_regression_trend"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "period": _period_schema(required=True, default=None),
                        "transform": MappingProxyType(
                            {
                                "type": "string",
                                "required": True,
                                "default": None,
                            }
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="macd",
                name="MACD",
                required_columns=("close",),
                output_templates=(
                    "macd_{fast_period}_{slow_period}",
                    "macd_signal_{fast_period}_{slow_period}_{signal_period}",
                    "macd_histogram_{fast_period}_{slow_period}_{signal_period}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.trend.macd:macd",
                parameter_schema=MappingProxyType(
                    {
                        "fast_period": _period_schema(required=False, default=12),
                        "signal_period": _period_schema(required=False, default=9),
                        "slow_period": _period_schema(required=False, default=26),
                    }
                ),
            ),
            _spec(
                indicator_id="cumulative_volume_delta",
                name="Cumulative Volume Delta",
                required_columns=("open", "close", "volume"),
                output_templates=(
                    "cvd_{window}",
                    "cvd_rolling_delta_{window}",
                    "cvd_buy_volume_{window}",
                    "cvd_sell_volume_{window}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.order_flow.cumulative_volume_delta:"
                    "cumulative_volume_delta"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "window": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="donchian_channels",
                name="Donchian Channel Levels",
                required_columns=("high", "low"),
                output_templates=(
                    "donchian_upper_{period}",
                    "donchian_lower_{period}",
                    "donchian_middle_{period}",
                ),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.structure.donchian_channels:"
                    "donchian_channels"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "include_current": _integer_schema(
                            required=False, default=1, minimum=0, maximum=1
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="gaps",
                name="Price Gap and Three-Bar Fair-Value Gap",
                required_columns=("high", "low"),
                output_templates=(
                    "gap_up",
                    "gap_down",
                    "fvg_up",
                    "fvg_down",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.structure.gaps:gaps",
                parameter_schema=MappingProxyType(
                    {
                        "min_gap": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e12
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="level_clustering",
                name="Structural-Level Clustering",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "level_cluster_price",
                    "level_cluster_weight",
                    "level_cluster_flag",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.structure.level_clustering:"
                    "level_clustering"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "half_life": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e12
                        ),
                        "lookback": _integer_schema(
                            required=True, default=None, minimum=5, maximum=1_000_000
                        ),
                        "tolerance": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e12
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="pivot_points",
                name="Traditional Pivot Points",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "pivot_points_p",
                    "pivot_points_r1",
                    "pivot_points_r2",
                    "pivot_points_r3",
                    "pivot_points_s1",
                    "pivot_points_s2",
                    "pivot_points_s3",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.structure.pivot_points:pivot_points",
                parameter_schema=MappingProxyType({}),
            ),
            _spec(
                indicator_id="pivots",
                name="Confirmed Swing High/Low Pivots",
                required_columns=("high", "low"),
                output_templates=(
                    "pivot_high_flag_{left}_{right}",
                    "pivot_high_price_{left}_{right}",
                    "pivot_low_flag_{left}_{right}",
                    "pivot_low_price_{left}_{right}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.structure.pivots:pivots",
                parameter_schema=MappingProxyType(
                    {
                        "left": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "right": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="volume_profile",
                name="Volume Profile POC and Value Area",
                required_columns=("close", "volume"),
                output_templates=(
                    "volume_profile_poc_{period}_{bins}",
                    "volume_profile_val_{period}_{bins}",
                    "volume_profile_vah_{period}_{bins}",
                ),
                warmup_policy="period",
                import_path=(
                    "app.services.indicators.structure.volume_profile:volume_profile"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "bins": _integer_schema(
                            required=True, default=None, minimum=1, maximum=10_000
                        ),
                        "period": _period_schema(required=True, default=None),
                        "value_area_fraction": _number_schema(
                            required=False,
                            default=0.70,
                            minimum=1e-9,
                            maximum=1.0,
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="supertrend",
                name="Supertrend",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "supertrend_line_{atr_period}",
                    "supertrend_direction_{atr_period}",
                    "supertrend_upper_{atr_period}",
                    "supertrend_lower_{atr_period}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.trend.supertrend:supertrend",
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "multiplier": _number_schema(
                            required=True,
                            default=None,
                            minimum=1e-12,
                            maximum=1_000_000.0,
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="amihud_illiquidity",
                name="Amihud Illiquidity",
                required_columns=("close", "volume"),
                output_templates=("amihud_illiquidity_{window}",),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.liquidity.amihud_illiquidity:"
                    "amihud_illiquidity"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "window": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="price_velocity",
                name="Log-Price Velocity",
                required_columns=("close",),
                output_templates=(
                    "price_velocity_{k}",
                    "price_velocity_direction_{k}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.market_speed.price_velocity:price_velocity"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "k": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "unit_seconds": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e12
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="momentum_acceleration",
                name="Momentum Acceleration",
                required_columns=("close",),
                output_templates=(
                    "price_acceleration_{k}",
                    "acceleration_state_{k}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.market_speed.momentum_acceleration:"
                    "momentum_acceleration"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "k": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "unit_seconds": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e12
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="volume_acceleration",
                name="Volume Acceleration",
                required_columns=("volume",),
                output_templates=("volume_acceleration_{window}_{k}",),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.market_speed.volume_acceleration:"
                    "volume_acceleration"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "k": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "unit_seconds": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e12
                        ),
                        "window": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="market_event_arrival_rate",
                name="Market-Event Arrival Rate",
                required_columns=("close",),
                output_templates=("events_per_second",),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.market_speed.market_event_arrival_rate:"
                    "market_event_arrival_rate"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "window_seconds": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e12
                        )
                    }
                ),
            ),
            _spec(
                indicator_id="volatility_expansion_rate",
                name="Volatility Expansion Rate",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "volatility_expansion_rate_{atr_period}_{k}",
                    "volatility_expansion_direction_{atr_period}_{k}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.market_speed.volatility_expansion_rate:"
                    "volatility_expansion_rate"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "k": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "unit_seconds": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e12
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="composite_market_speed_gauge",
                name="Composite Market Speed Gauge",
                required_columns=("open", "high", "low", "close", "volume"),
                output_templates=(
                    "composite_score_{k}_{volume_window}_{atr_period}_{z_window}",
                    "speed_band_{k}_{volume_window}_{atr_period}_{z_window}",
                    "speed_direction_{k}_{volume_window}_{atr_period}_{z_window}",
                    "speed_contribution_price_velocity_{k}_{volume_window}_"
                    "{atr_period}_{z_window}",
                    "speed_contribution_momentum_acceleration_{k}_{volume_window}_"
                    "{atr_period}_{z_window}",
                    "speed_contribution_volume_acceleration_{k}_{volume_window}_"
                    "{atr_period}_{z_window}",
                    "speed_contribution_volatility_expansion_{k}_{volume_window}_"
                    "{atr_period}_{z_window}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.market_speed."
                    "composite_market_speed_gauge:composite_market_speed_gauge"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "k": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "unit_seconds": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e12
                        ),
                        "volume_window": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "weight_momentum_acceleration": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                        "weight_price_velocity": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                        "weight_volatility_expansion": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                        "weight_volume_acceleration": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                        "z_max": _number_schema(
                            required=True, default=None, minimum=1e-9, maximum=1e9
                        ),
                        "z_window": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000_000
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="adx_dmi_regime",
                name="ADX/DMI Trend Regime",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "regime_candidate_{period}",
                    "trend_strength_{period}",
                    "regime_direction_{period}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.regime.adx_dmi_regime:adx_dmi_regime",
                parameter_schema=MappingProxyType(
                    {
                        "adx_range": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "adx_trend": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="choppiness_regime",
                name="Choppiness Index Regime",
                required_columns=("high", "low", "close"),
                output_templates=("choppiness_{period}", "choppiness_state_{period}"),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.regime.choppiness_regime:choppiness_regime"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "lower_threshold": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "period": _period_schema(required=True, default=None),
                        "upper_threshold": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="hurst_regime",
                name="Hurst Persistence Regime",
                required_columns=("close",),
                output_templates=("hurst_exponent_{window}", "hurst_state_{window}"),
                warmup_policy="custom",
                import_path="app.services.indicators.regime.hurst_regime:hurst_regime",
                parameter_schema=MappingProxyType(
                    {
                        "lower_threshold": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                        "max_scale": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000_000
                        ),
                        "min_scale": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000_000
                        ),
                        "scale_count": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000
                        ),
                        "upper_threshold": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                        "window": _integer_schema(
                            required=True, default=None, minimum=4, maximum=1_000_000
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="donchian_breakout_regime",
                name="Donchian Breakout Regime",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "breakout_state_{period}_{atr_period}",
                    "breached_level_{period}_{atr_period}",
                    "breakout_distance_atr_{period}_{atr_period}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.regime.donchian_breakout_regime:"
                    "donchian_breakout_regime"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "period": _period_schema(required=True, default=None),
                    }
                ),
            ),
            _spec(
                indicator_id="volatility_liquidity_stress_regime",
                name="Volatility-Liquidity Stress Regime",
                required_columns=("close", "volume"),
                output_templates=(
                    "stress_regime_{vol_reference_period}_{vol_period}_{amihud_window}",
                    "stress_volatility_percentile_{vol_reference_period}_{vol_period}_"
                    "{amihud_window}",
                    "stress_illiquidity_percentile_{vol_reference_period}_"
                    "{vol_period}_{amihud_window}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.regime."
                    "volatility_liquidity_stress_regime:"
                    "volatility_liquidity_stress_regime"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "amihud_window": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "p_illiquidity_extreme": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "p_illiquidity_high": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "p_vol_extreme": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "vol_period": _period_schema(required=True, default=None),
                        "vol_reference_period": _period_schema(
                            required=True, default=None
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="final_regime_resolver",
                name="Final Regime Resolver",
                required_columns=("high", "low", "close", "volume"),
                output_templates=("primary_regime", "primary_regime_confidence"),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.regime.final_regime_resolver:"
                    "final_regime_resolver"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "adx_period": _period_schema(required=True, default=None),
                        "adx_range": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "adx_trend": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "amihud_window": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "chop_lower_threshold": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "chop_period": _period_schema(required=True, default=None),
                        "chop_upper_threshold": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "donchian_period": _period_schema(required=True, default=None),
                        "p_illiquidity_extreme": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "p_illiquidity_high": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "p_vol_extreme": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=100.0
                        ),
                        "vol_period": _period_schema(required=True, default=None),
                        "vol_reference_period": _period_schema(
                            required=True, default=None
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="double_top_bottom",
                name="Double Top and Double Bottom",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "double_top_state_{left}_{right}_{atr_period}",
                    "double_top_neckline_{left}_{right}_{atr_period}",
                    "double_bottom_state_{left}_{right}_{atr_period}",
                    "double_bottom_neckline_{left}_{right}_{atr_period}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.patterns.double_top_bottom:"
                    "double_top_bottom"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "d_min_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "left": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "m_confirm": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "right": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "tau_price": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="head_and_shoulders",
                name="Head and Shoulders and Inverse",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "head_shoulders_state_{left}_{right}_{atr_period}",
                    "inverse_head_shoulders_state_{left}_{right}_{atr_period}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.patterns.head_and_shoulders:"
                    "head_and_shoulders"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "d_head_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "left": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "m_confirm": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "right": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "tau_shoulder": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="triangle",
                name="Triangle",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "triangle_type_{left}_{right}_{atr_period}",
                    "triangle_breakout_state_{left}_{right}_{atr_period}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.patterns.triangle:triangle",
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "left": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "lookback": _integer_schema(
                            required=True, default=None, minimum=4, maximum=1_000_000
                        ),
                        "min_touches": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000
                        ),
                        "right": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "slope_flat": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="wedge",
                name="Rising and Falling Wedge",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "wedge_type_{left}_{right}_{atr_period}",
                    "wedge_breakout_state_{left}_{right}_{atr_period}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.patterns.wedge:wedge",
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "left": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "lookback": _integer_schema(
                            required=True, default=None, minimum=4, maximum=1_000_000
                        ),
                        "min_touches": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000
                        ),
                        "right": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="rectangle",
                name="Rectangle and Trading Range",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "rectangle_state_{left}_{right}_{atr_period}",
                    "rectangle_upper_{left}_{right}_{atr_period}",
                    "rectangle_lower_{left}_{right}_{atr_period}",
                ),
                warmup_policy="custom",
                import_path="app.services.indicators.patterns.rectangle:rectangle",
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "left": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "lookback": _integer_schema(
                            required=True, default=None, minimum=4, maximum=1_000_000
                        ),
                        "min_touches": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000
                        ),
                        "right": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "slope_flat": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "tolerance": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="flag_pennant",
                name="Flag and Pennant",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "consolidation_type_{atr_period}_{impulse_lookback}_"
                    "{consolidation_bars}",
                    "consolidation_breakout_state_{atr_period}_{impulse_lookback}_"
                    "{consolidation_bars}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.patterns.flag_pennant:flag_pennant"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "consolidation_bars": _integer_schema(
                            required=True, default=None, minimum=2, maximum=1_000_000
                        ),
                        "impulse_lookback": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "impulse_min_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "retrace_max": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1.0
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="breakout_retest",
                name="Breakout and Retest",
                required_columns=("high", "low", "close"),
                output_templates=(
                    "breakout_retest_bullish_state_{left}_{right}_{atr_period}",
                    "breakout_retest_bearish_state_{left}_{right}_{atr_period}",
                ),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.patterns.breakout_retest:breakout_retest"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "beta_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "left": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "m": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "right": _integer_schema(
                            required=True, default=None, minimum=1, maximum=1_000_000
                        ),
                        "tau_price": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                    }
                ),
            ),
            _spec(
                indicator_id="three_bar_reversal",
                name="Three-Bar Reversal",
                required_columns=("open", "high", "low", "close"),
                output_templates=("reversal_state_{atr_period}",),
                warmup_policy="custom",
                import_path=(
                    "app.services.indicators.patterns.three_bar_reversal:"
                    "three_bar_reversal"
                ),
                parameter_schema=MappingProxyType(
                    {
                        "atr_period": _period_schema(required=True, default=None),
                        "body_min_atr": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                        "confirm_fraction": _number_schema(
                            required=True, default=None, minimum=0.0, maximum=1e9
                        ),
                    }
                ),
            ),
        )
    }
)

_REGISTRY_ORDER: tuple[str, ...] = (
    "adx",
    "adr",
    "adx_dmi_regime",
    "aggressive_trade_imbalance",
    "amihud_illiquidity",
    "anchored_vwap",
    "aroon",
    "atr",
    "atr_percent",
    "bollinger_bands",
    "bollinger_bandwidth",
    "breakout_retest",
    "choppiness_regime",
    "cmf",
    "composite_market_speed_gauge",
    "cumulative_volume_delta",
    "doji",
    "donchian_breakout_regime",
    "donchian_channels",
    "double_top_bottom",
    "ema",
    "ema_slope",
    "engulfing",
    "ewma_volatility",
    "final_regime_resolver",
    "flag_pennant",
    "garman_klass_volatility",
    "gaps",
    "head_and_shoulders",
    "hull_ma",
    "hurst_regime",
    "inside_bar",
    "level_clustering",
    "linear_regression_trend",
    "macd",
    "market_event_arrival_rate",
    "mfi",
    "momentum_acceleration",
    "obv",
    "parkinson_volatility",
    "pinbar",
    "pivot_points",
    "pivots",
    "price_velocity",
    "price_volume_distribution",
    "rectangle",
    "rogers_satchell_volatility",
    "rolling_volatility",
    "rsi",
    "sma",
    "standard_deviation",
    "supertrend",
    "three_bar_reversal",
    "triangle",
    "volatility_expansion_rate",
    "volatility_liquidity_stress_regime",
    "volatility_of_volatility",
    "volatility_percentile",
    "volume_acceleration",
    "volume_profile",
    "wedge",
    "williams_r",
    "wma",
    "zigzag",
)


@guard_public_boundary
def get_indicator(indicator_id: str) -> IndicatorSpec:
    """Resolve one official indicator ID to its immutable spec.

    Args:
        indicator_id: Candidate official lowercase indicator identifier.

    Returns:
        The immutable official ``IndicatorSpec``.

    Raises:
        IndicatorError: ``IND_UNSUPPORTED_INDICATOR`` if the ID is not one
            of the sixty-four official built-ins.
    """
    logger.info("Resolving official indicator spec for %s", indicator_id)
    spec = _REGISTRY.get(indicator_id)
    if spec is None:
        raise IndicatorError(
            IndicatorErrorCode.IND_UNSUPPORTED_INDICATOR,
            "requested indicator is not an official built-in",
            {"indicator_id": str(indicator_id)},
        )
    return spec


@guard_public_boundary
def list_indicators() -> tuple[IndicatorSpec, ...]:
    """List every official spec in stable indicator-ID order.

    Args:
        None.

    Returns:
            An immutable tuple of official specs with no mutable registry
            handle exposed.

    Raises:
        None.
    """
    logger.info("Listing official indicator specs")
    return tuple(_REGISTRY[indicator_id] for indicator_id in _REGISTRY_ORDER)


@guard_public_boundary
def get_capability_matrix() -> tuple[Mapping[str, object], ...]:
    """Build the JSON/YAML-compatible official capability matrix.

    Args:
        None.

    Returns:
            An immutable tuple of frozen capability records in registry order,
            each with exactly the approved keys in canonical order.

    Raises:
        None.
    """
    logger.info("Building official indicator capability matrix")
    records = []
    for indicator_id in _REGISTRY_ORDER:
        spec = _REGISTRY[indicator_id]
        # Every official calculator uses both NumPy and pandas for its
        # vectorized formula (verified against each leaf file's imports).
        dependencies = ("numpy", "pandas")
        records.append(
            MappingProxyType(
                {
                    "indicator_id": spec.indicator_id,
                    "indicator_version": spec.indicator_version,
                    "formula_version": spec.formula_version,
                    "tier": spec.tier,
                    "batch": True,
                    "vectorized": spec.vectorized,
                    "multi_symbol": spec.multi_symbol,
                    "multi_timeframe": spec.multi_timeframe,
                    "unsupported_optional_modes": _UNSUPPORTED_OPTIONAL_MODES,
                    "dependencies": dependencies,
                    "unsupported_codes": _UNSUPPORTED_CODES,
                    "official_workflow_eligibility": spec.workflow_eligibility,
                }
            )
        )
    return tuple(records)


__all__ = ["get_capability_matrix", "get_indicator", "list_indicators"]
