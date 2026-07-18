"""Immutable official Indicators registry and capability matrix.

Describes the twenty official built-in indicators and the Core-supported
execution modes. The registry stores no runtime registrations, performs no
plugin discovery, and never imports a feature implementation module.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.services.indicators.core.contracts import IndicatorSpec
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.utils import logger

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
    """
    logger.debug("Building period parameter schema (required=%s)", required)
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
    """
    logger.debug("Building numeric parameter schema (required=%s)", required)
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
    """
    logger.debug("Building integer parameter schema (required=%s)", required)
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
    """
    logger.debug("Building official IndicatorSpec for %s", indicator_id)
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
                output_templates=("atr_{period}",),
                warmup_policy="period",
                import_path="app.services.indicators.volatility.atr:atr",
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
                import_path="app.services.indicators.candles.doji:doji",
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
                import_path="app.services.indicators.candles.engulfing:engulfing",
                parameter_schema=MappingProxyType({}),
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
                import_path="app.services.indicators.candles.inside_bar:inside_bar",
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
                indicator_id="pinbar",
                name="Pinbar",
                required_columns=("open", "high", "low", "close"),
                output_templates=("pinbar",),
                warmup_policy="none",
                import_path="app.services.indicators.candles.pinbar:pinbar",
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
                indicator_id="rolling_volatility",
                name="Rolling Volatility",
                required_columns=("source",),
                period_required=True,
                period_default=None,
                output_templates=(
                    "rolling_volatility_{period}",
                    "rolling_volatility_{source}_{period}",
                ),
                warmup_policy="period_plus_one",
                import_path=(
                    "app.services.indicators.volatility.rolling_volatility:"
                    "rolling_volatility"
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
        )
    }
)

_REGISTRY_ORDER: tuple[str, ...] = (
    "adx",
    "adr",
    "atr",
    "bollinger_bands",
    "cmf",
    "doji",
    "ema",
    "engulfing",
    "hull_ma",
    "inside_bar",
    "mfi",
    "obv",
    "pinbar",
    "price_volume_distribution",
    "rolling_volatility",
    "rsi",
    "sma",
    "standard_deviation",
    "williams_r",
    "wma",
)


def get_indicator(indicator_id: str) -> IndicatorSpec:
    """Resolve one official indicator ID to its immutable spec.

    Args:
        indicator_id: Candidate official lowercase indicator identifier.

    Returns:
        The immutable official ``IndicatorSpec``.

    Raises:
        IndicatorError: ``IND_UNSUPPORTED_INDICATOR`` if the ID is not one
            of the twenty official built-ins.
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


def list_indicators() -> tuple[IndicatorSpec, ...]:
    """List every official spec in stable indicator-ID order.

    Returns:
        An immutable tuple of official specs with no mutable registry
        handle exposed.
    """
    logger.info("Listing official indicator specs")
    return tuple(_REGISTRY[indicator_id] for indicator_id in _REGISTRY_ORDER)


def get_capability_matrix() -> tuple[Mapping[str, object], ...]:
    """Build the JSON/YAML-compatible official capability matrix.

    Returns:
        An immutable tuple of frozen capability records in registry order,
        each with exactly the approved keys in canonical order.
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
