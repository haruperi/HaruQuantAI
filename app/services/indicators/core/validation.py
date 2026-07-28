"""Fail-fast whole-request validation preceding official calculation.

Resolves the official spec and atomically validates configuration,
parameters, resource limits, dataset identity, and formula-relevant
invariants before any private projection or vectorized formula work.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from datetime import timedelta
from typing import cast

import pandas as pd

from app.services.data import (
    MarketDataset,
    OHLCVRecord,
)
from app.services.indicators.core.contracts import (
    IndicatorConfig,
    IndicatorSpec,
    WarmupRequirement,
)
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.registry import get_indicator
from app.utils import logger

MAX_INPUT_ROWS = 1_000_000

_SNAKE_CASE_KEY = re.compile(r"^[a-z][a-z0-9_]*$")
_VALID_SOURCES = ("open", "high", "low", "close")
_FIXED_RESULT_COLUMNS = (
    "symbol",
    "available_at",
    "computed_from_start",
    "computed_from_end",
    "source_timeframe",
    "data_quality_status",
    "data_quality_score",
    "unavailable_reason",
)
_SOURCE_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")


def _validate_config_identity(indicator_id: str, config: IndicatorConfig) -> None:
    """Validate that config identity and fixed policy fields agree.

    Args:
        indicator_id: Requested official indicator identifier.
        config: The candidate calculation configuration.

    Raises:
        IndicatorError: ``IND_INVALID_CONFIG`` if the config disagrees with
            the requested indicator or a fixed policy field is non-approved.
    """
    if config.indicator_id != indicator_id:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "config indicator_id disagrees with the requested indicator",
            {"indicator_id": indicator_id},
        )
    if (
        config.column_conflict_policy != "error"
        or config.availability_policy != "source_available_at"
        or config.quality_policy != "propagate_dataset"
        or config.error_mode != "raise"
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "config carries a non-approved fixed policy value",
            {"indicator_id": indicator_id},
        )


def _validate_output_mode(config: IndicatorConfig) -> None:
    """Validate that the output mode is exactly ``values``.

    Args:
        config: The candidate calculation configuration.

    Raises:
        IndicatorError: ``IND_INVALID_OUTPUT_MODE`` otherwise.
    """
    if config.output_mode != "values":
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_OUTPUT_MODE,
            "output_mode must be exactly values",
        )


def _validate_precision_dtype(config: IndicatorConfig) -> None:
    """Validate that the precision dtype is exactly ``float64``.

    Args:
        config: The candidate calculation configuration.

    Raises:
        IndicatorError: ``IND_UNSUPPORTED_DTYPE`` otherwise.
    """
    if config.precision_dtype != "float64":
        raise IndicatorError(
            IndicatorErrorCode.IND_UNSUPPORTED_DTYPE,
            "precision_dtype must be exactly float64",
        )


def _validate_formula_version(spec: IndicatorSpec, config: IndicatorConfig) -> None:
    """Validate that the config formula version matches the registry.

    Args:
        spec: The resolved official spec.
        config: The candidate calculation configuration.

    Raises:
        IndicatorError: ``IND_FORMULA_VERSION_MISMATCH`` otherwise.
    """
    if config.formula_version != spec.formula_version:
        raise IndicatorError(
            IndicatorErrorCode.IND_FORMULA_VERSION_MISMATCH,
            "config formula_version disagrees with the official spec",
            {"indicator_id": spec.indicator_id},
        )


def _validate_one_declared_parameter(
    name: str, schema: Mapping[str, object], value: float | str | None
) -> None:
    """Validate one config parameter against its declared schema entry.

    Generalizes period-only validation to any declared parameter (for
    example a formula-specific ``threshold`` or ``std_dev`` multiplier),
    using the same ``type``/``minimum``/``maximum``/``required`` schema
    shape ``_period_schema`` already produces for ``period``.

    Args:
        name: The declared parameter's canonical key.
        schema: The parameter's frozen schema entry.
        value: The candidate value supplied in ``config.parameters``, or
            ``None`` if the caller omitted it.

    Raises:
        IndicatorError: ``IND_INVALID_PARAMETER`` if a required parameter is
            missing, its type disagrees with the schema, or it falls outside
            the declared minimum/maximum.
    """
    if value is None:
        if schema.get("required", False):
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_PARAMETER,
                "parameter is required but was not supplied",
                {"parameter": name},
            )
        return
    declared_type = schema.get("type")
    if declared_type == "integer" and (
        isinstance(value, bool) or not isinstance(value, int)
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "parameter must be a supplied integer",
            {"parameter": name},
        )
    if declared_type == "number" and (
        isinstance(value, bool) or not isinstance(value, (int, float))
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "parameter must be a supplied number",
            {"parameter": name},
        )
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    if minimum is not None and value < minimum:  # type: ignore[operator]
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "parameter is below the declared minimum",
            {"parameter": name},
        )
    if maximum is not None and value > maximum:  # type: ignore[operator]
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "parameter is above the declared maximum",
            {"parameter": name},
        )


def _validate_parameters(spec: IndicatorSpec, config: IndicatorConfig) -> None:
    """Validate canonical parameter shape, declared parameters, and source.

    Args:
        spec: The resolved official spec.
        config: The candidate calculation configuration.

    Raises:
        IndicatorError: ``IND_INVALID_PARAMETER`` if keys are malformed, a
            declared parameter is missing/invalid, an undeclared parameter
            is supplied, or the source is invalid for this indicator.
    """
    keys = [key for key, _ in config.parameters]
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "parameters must be key-sorted with unique keys",
        )
    for key in keys:
        if not _SNAKE_CASE_KEY.fullmatch(key):
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_PARAMETER,
                "parameter keys must be lowercase snake_case",
                {"key": key},
            )
    provided = dict(config.parameters)
    for name, schema in spec.parameter_schema.items():
        _validate_one_declared_parameter(name, schema, provided.get(name))  # type: ignore[arg-type]
    undeclared = tuple(key for key in keys if key not in spec.parameter_schema)
    if undeclared:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "parameters include an undeclared key",
            {"keys": undeclared},
        )
    requires_source = "source" in spec.required_columns
    if requires_source and config.source not in _VALID_SOURCES:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "source must be one of open, high, low, close",
            {"source": str(config.source)},
        )
    if not requires_source and config.source is not None:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "fixed-OHLC indicators do not accept a source",
            {"indicator_id": spec.indicator_id},
        )


def _validate_row_limit(data: MarketDataset) -> None:
    """Validate that the input row count does not exceed the approved limit.

    Args:
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_RESOURCE_LIMIT_EXCEEDED`` otherwise.
    """
    if len(data.records) > MAX_INPUT_ROWS:
        raise IndicatorError(
            IndicatorErrorCode.IND_RESOURCE_LIMIT_EXCEEDED,
            "input row count exceeds the approved maximum",
            {"row_count": len(data.records)},
        )


def _validate_input_schema(data: MarketDataset) -> None:
    """Validate dataset contract identity, bars-only kind, and quality.

    Args:
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_INVALID_INPUT_SCHEMA`` if the contract
            version, schema ID, data kind, record types, or quality status
            are not approved for Indicators.
    """
    if data.contract_version != "v1" or data.schema_id != "data.market_dataset.v1":
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA,
            "dataset contract identity is not MarketDataset v1",
        )
    if data.data_kind != "bars" or any(
        not isinstance(record, OHLCVRecord) for record in data.records
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA,
            "dataset must contain only bar records",
        )
    if data.quality_report.quality_status == "failed":
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA,
            "dataset quality status is failed",
        )


def _validate_adr_timeframe(indicator_id: str, data: MarketDataset) -> None:
    """Validate that ADR receives only a ``D1`` source dataset.

    Args:
        indicator_id: Requested official indicator identifier.
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_UNSUPPORTED_TIMEFRAME`` if ADR is requested
            against a non-``D1`` dataset.
    """
    if indicator_id == "adr" and data.timeframe != "D1":
        raise IndicatorError(
            IndicatorErrorCode.IND_UNSUPPORTED_TIMEFRAME,
            "adr requires an exact D1 source timeframe",
            {"timeframe": str(data.timeframe)},
        )


def _validate_sufficient_data(data: MarketDataset) -> None:
    """Validate that the dataset contains at least one usable record.

    Args:
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_INSUFFICIENT_DATA`` if the dataset is empty.
    """
    if len(data.records) == 0:
        raise IndicatorError(
            IndicatorErrorCode.IND_INSUFFICIENT_DATA,
            "dataset contains no usable records",
        )


def _resolve_price_fields(
    spec: IndicatorSpec, config: IndicatorConfig
) -> tuple[str, ...]:
    """Resolve an indicator's required columns to concrete record fields.

    Args:
        spec: The resolved official spec.
        config: The candidate calculation configuration.

    Returns:
        The concrete OHLC record field names this indicator reads.
    """
    return tuple(
        config.source if column == "source" and config.source else column
        for column in spec.required_columns
    )


def _validate_required_columns(spec: IndicatorSpec, config: IndicatorConfig) -> None:
    """Validate that required fixed/source columns resolve to real fields.

    Args:
        spec: The resolved official spec.
        config: The candidate calculation configuration.

    Raises:
        IndicatorError: ``IND_MISSING_REQUIRED_COLUMN`` if a resolved field
            is not one of the dataset's always-present OHLCV columns.
    """
    fields = _resolve_price_fields(spec, config)
    missing = tuple(field for field in fields if field not in _SOURCE_OHLCV_COLUMNS)
    if missing:
        raise IndicatorError(
            IndicatorErrorCode.IND_MISSING_REQUIRED_COLUMN,
            "one or more required columns are not present",
            {"columns": missing},
        )


def _validate_timezone(data: MarketDataset) -> None:
    """Validate that every record timestamp is UTC-aware.

    Args:
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_INVALID_TIMEZONE`` otherwise.
    """
    for record in data.records:
        if record.timestamp.tzinfo is None or record.timestamp.utcoffset() != timedelta(
            0
        ):
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_TIMEZONE,
                "record timestamps must be UTC-aware",
            )


def _validate_no_ambiguous_timestamps(data: MarketDataset) -> None:
    """Validate that timestamps round-trip uniquely into a pandas index.

    Args:
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_AMBIGUOUS_TIMESTAMP`` if conversion fails or
            round-trips to a different value or row count.
    """
    timestamps = [record.timestamp for record in data.records]
    try:
        index = pd.DatetimeIndex(timestamps)
    except (ValueError, TypeError) as error:
        raise IndicatorError(
            IndicatorErrorCode.IND_AMBIGUOUS_TIMESTAMP,
            "timestamps do not convert to an unambiguous pandas index",
        ) from error
    if len(index) != len(timestamps) or any(
        index[position].to_pydatetime() != timestamps[position]
        for position in range(len(timestamps))
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_AMBIGUOUS_TIMESTAMP,
            "timestamps do not round-trip uniquely into a pandas index",
        )


def _validate_unique_timestamps(data: MarketDataset) -> None:
    """Validate that record timestamps are unique.

    Args:
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_DUPLICATE_TIMESTAMP`` otherwise.
    """
    timestamps = [record.timestamp for record in data.records]
    if len(set(timestamps)) != len(timestamps):
        raise IndicatorError(
            IndicatorErrorCode.IND_DUPLICATE_TIMESTAMP,
            "record timestamps must be unique",
        )


def _validate_monotonic_timestamps(data: MarketDataset) -> None:
    """Validate that record timestamps are strictly increasing.

    Args:
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_NON_MONOTONIC_TIME`` otherwise.
    """
    timestamps = [record.timestamp for record in data.records]
    if timestamps != sorted(timestamps):
        raise IndicatorError(
            IndicatorErrorCode.IND_NON_MONOTONIC_TIME,
            "record timestamps must be strictly increasing",
        )


def _validate_finite_numeric(
    spec: IndicatorSpec, config: IndicatorConfig, data: MarketDataset
) -> None:
    """Validate that selected numeric values convert to finite float64.

    Args:
        spec: The resolved official spec.
        config: The candidate calculation configuration.
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_UNSUPPORTED_DTYPE`` if a selected value does
            not convert to a finite float.
    """
    fields = _resolve_price_fields(spec, config)
    for record in data.records:
        for field in fields:
            decimal_value = getattr(record, field)
            try:
                float_value = float(decimal_value)
            except (OverflowError, ValueError) as error:
                raise IndicatorError(
                    IndicatorErrorCode.IND_UNSUPPORTED_DTYPE,
                    "selected value does not convert to a finite float64",
                    {"field": field},
                ) from error
            if not math.isfinite(float_value):
                raise IndicatorError(
                    IndicatorErrorCode.IND_UNSUPPORTED_DTYPE,
                    "selected value does not convert to a finite float64",
                    {"field": field},
                )


def _validate_formula_specific_invariants(
    indicator_id: str, config: IndicatorConfig, data: MarketDataset
) -> None:
    """Validate formula-specific OHLC/positive-price invariants.

    Args:
        indicator_id: Requested official indicator identifier.
        config: The candidate calculation configuration.
        data: The candidate input dataset.

    Raises:
        IndicatorError: ``IND_INVALID_OHLC`` if rolling_volatility receives
            a non-positive selected price.
    """
    if indicator_id != "rolling_volatility":
        return
    source = config.source or "close"
    for record in data.records:
        if getattr(record, source) <= 0:
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_OHLC,
                "rolling_volatility requires strictly positive source prices",
            )


def _resolve_output_columns(
    spec: IndicatorSpec, config: IndicatorConfig
) -> tuple[str, ...]:
    """Resolve the deterministic output column names for one config.

    Args:
        spec: The resolved official spec.
        config: The candidate calculation configuration.

    Returns:
        The resolved, deterministic output column names in canonical order.
    """
    format_kwargs = dict(config.parameters)
    templates = spec.output_templates
    if len(templates) > 1 and config.source is not None:
        default_template, source_template = templates
        if config.source == "close":
            return (default_template.format(**format_kwargs),)
        return (source_template.format(**format_kwargs, source=config.source),)
    return tuple(template.format(**format_kwargs) for template in templates)


def _validate_output_column_names(output_columns: tuple[str, ...]) -> None:
    """Validate that resolved output names are lowercase snake_case.

    Args:
        output_columns: The resolved output column names.

    Raises:
        IndicatorError: ``IND_INVALID_OUTPUT_COLUMN`` otherwise.
    """
    for column in output_columns:
        if not _SNAKE_CASE_KEY.fullmatch(column):
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_OUTPUT_COLUMN,
                "resolved output column is not lowercase snake_case",
                {"column": column},
            )


def _validate_no_output_collision(output_columns: tuple[str, ...]) -> None:
    """Validate that resolved outputs do not collide with reserved columns.

    Args:
        output_columns: The resolved output column names.

    Raises:
        IndicatorError: ``IND_OUTPUT_COLUMN_CONFLICT`` otherwise.
    """
    reserved = set(_FIXED_RESULT_COLUMNS) | set(_SOURCE_OHLCV_COLUMNS)
    colliding = tuple(column for column in output_columns if column in reserved)
    if colliding:
        raise IndicatorError(
            IndicatorErrorCode.IND_OUTPUT_COLUMN_CONFLICT,
            "resolved output columns collide with reserved columns",
            {"columns": colliding},
        )


@guard_public_boundary
def get_warmup_requirement(
    indicator_id: str,
    config: IndicatorConfig,
) -> WarmupRequirement:
    """Resolve the exact normalized history requirement for one config.

    Args:
        indicator_id: Requested official indicator identifier.
        config: Complete calculation configuration for the indicator.

    Returns:
        The immutable formula-specific warmup requirement.

    Raises:
        IndicatorError: If the indicator or configuration is invalid.
    """
    logger.info("Resolving warmup requirement for %s", indicator_id)
    spec = _unwrap_indicator_response(get_indicator(indicator_id))
    _validate_config_identity(indicator_id, config)
    _validate_output_mode(config)
    _validate_precision_dtype(config)
    _validate_formula_version(spec, config)
    _validate_parameters(spec, config)

    parameters = dict(config.parameters)
    period_value = parameters.get("period")
    if period_value is None:
        period_schema = spec.parameter_schema.get("period")
        if isinstance(period_schema, Mapping):
            period_value = period_schema.get("default")
    period = period_value if isinstance(period_value, int) else None
    requires_period = (
        spec.warmup_policy
        in {
            "period",
            "period_plus_one",
            "two_period",
        }
        or indicator_id == "hull_ma"
    )
    if requires_period and period is None:
        raise IndicatorError(
            IndicatorErrorCode.IND_INTERNAL_ERROR,
            "official warmup policy is missing period metadata",
            {"indicator_id": indicator_id},
        )
    resolved_period = cast("int", period)

    if spec.warmup_policy == "none":
        minimum_observations = 1
    elif spec.warmup_policy == "period":
        minimum_observations = resolved_period
    elif spec.warmup_policy == "period_plus_one":
        minimum_observations = resolved_period + 1
    elif spec.warmup_policy == "two_period":
        minimum_observations = 2 * resolved_period
    elif indicator_id == "hull_ma":
        minimum_observations = resolved_period + math.isqrt(resolved_period) - 1
    else:
        minimum_observations = 2

    required_columns = tuple(
        cast("str", config.source) if column == "source" else column
        for column in spec.required_columns
    )
    return WarmupRequirement(
        indicator_id=spec.indicator_id,
        formula_version=spec.formula_version,
        minimum_observations=minimum_observations,
        source_timeframe="D1" if indicator_id == "adr" else None,
        required_columns=required_columns,
        availability_basis="source_available_at",
    )


@guard_public_boundary
def validate_indicator(
    indicator_id: str, data: MarketDataset, config: IndicatorConfig
) -> IndicatorSpec:
    """Resolve and atomically validate one official batch calculation request.

    Args:
        indicator_id: Requested official indicator identifier.
        data: One immutable ``MarketDataset v1``.
        config: The complete, validated calculation configuration.

    Returns:
        The resolved official ``IndicatorSpec``.

    Raises:
        IndicatorError: The first deterministic Core validation failure in
            the approved precedence order.
    """
    logger.info("Validating indicator request for %s", indicator_id)
    spec = _unwrap_indicator_response(get_indicator(indicator_id))
    _validate_config_identity(indicator_id, config)
    _validate_output_mode(config)
    _validate_precision_dtype(config)
    _validate_formula_version(spec, config)
    _validate_parameters(spec, config)
    _validate_row_limit(data)
    _validate_input_schema(data)
    _validate_adr_timeframe(indicator_id, data)
    _validate_sufficient_data(data)
    _validate_required_columns(spec, config)
    _validate_timezone(data)
    _validate_no_ambiguous_timestamps(data)
    _validate_unique_timestamps(data)
    _validate_monotonic_timestamps(data)
    _validate_finite_numeric(spec, config, data)
    _validate_formula_specific_invariants(indicator_id, config, data)
    output_columns = _resolve_output_columns(spec, config)
    _validate_output_column_names(output_columns)
    _validate_no_output_collision(output_columns)
    return spec


__all__ = ["validate_indicator"]
