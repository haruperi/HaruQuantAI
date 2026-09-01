# ruff: noqa: C901, PLR0911
"""Validated JSON-safe IndicatorSnapshot v1 transport."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, cast

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_json
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)

logger = get_logger(__name__)

_SCHEMA = "indicators.indicator_snapshot.v1"
_MAX_EVIDENCE_REFS = 20
_FIELDS = {
    "schema",
    "indicator_id",
    "value",
    "unit",
    "state",
    "observed_at",
    "source_start",
    "source_end",
    "complete",
    "confidence",
    "data_health",
    "evidence_refs",
}


def _utc_text(value: datetime, field: str) -> str:
    """Return a canonical UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Field name used in safe diagnostics.

    Returns:
        ISO-8601 UTC timestamp text.

    Raises:
        IndicatorError: If the timestamp is not aware UTC.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_TIMEZONE,
            "snapshot timestamps must be aware UTC",
            {"field": field},
        )
    return value.isoformat().replace("+00:00", "Z")


def _parse_utc(value: object, field: str) -> datetime:
    """Parse one canonical UTC timestamp.

    Args:
        value: Candidate timestamp text.
        field: Field name used in safe diagnostics.

    Returns:
        Parsed aware UTC timestamp.

    Raises:
        IndicatorError: If the value is not canonical UTC text.
    """
    if not isinstance(value, str) or not value.endswith("Z"):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot timestamp must use canonical UTC text",
            {"field": field},
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot timestamp is invalid",
            {"field": field},
        ) from error
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot timestamp must be UTC",
            {"field": field},
        )
    return parsed


def _validated_mapping(value: Mapping[str, object]) -> dict[str, Any]:
    """Validate and detach an IndicatorSnapshot mapping.

    Args:
        value: Candidate snapshot mapping.

    Returns:
        Detached validated JSON-safe mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails.
    """
    if set(value) != _FIELDS or value.get("schema") != _SCHEMA:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot fields or schema are invalid",
        )
    for field in ("indicator_id", "unit", "state", "data_health"):
        item = value[field]
        if not isinstance(item, str) or not item.strip():
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_SNAPSHOT,
                "snapshot text field is invalid",
                {"field": field},
            )
    number = value["value"]
    if number is not None and (
        isinstance(number, bool)
        or not isinstance(number, int | float)
        or not math.isfinite(float(number))
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot value must be finite or null",
        )
    confidence = value["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, int | float)
        or not math.isfinite(float(confidence))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot confidence must be within zero and one",
        )
    if not isinstance(value["complete"], bool):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot completeness must be boolean",
        )
    refs = value["evidence_refs"]
    if (
        not isinstance(refs, list | tuple)
        or len(refs) > _MAX_EVIDENCE_REFS
        or any(not isinstance(ref, str) or not ref.strip() for ref in refs)
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot evidence references are invalid",
        )
    observed = _parse_utc(value["observed_at"], "observed_at")
    source_start = _parse_utc(value["source_start"], "source_start")
    source_end = _parse_utc(value["source_end"], "source_end")
    if source_start > source_end or source_end > observed:
        raise IndicatorError(
            IndicatorErrorCode.IND_LOOKAHEAD_RISK,
            "snapshot source range is not causal",
        )
    detached = dict(value)
    detached["value"] = None if number is None else float(number)
    detached["confidence"] = float(confidence)
    detached["evidence_refs"] = list(refs)
    canonical_json(detached, max_items=None)
    return detached


@guard_public_boundary
def build_indicator_snapshot(
    *,
    indicator_id: str,
    value: float | None,
    unit: str,
    state: str,
    observed_at: datetime,
    source_start: datetime,
    source_end: datetime,
    complete: bool,
    confidence: float,
    data_health: str,
    evidence_refs: Sequence[str] = (),
) -> Mapping[str, Any]:
    """Build one validated IndicatorSnapshot v1 mapping.

    Args:
        indicator_id: Stable indicator identifier.
        value: Finite produced value, or null when explicitly unavailable.
        unit: Explicit measurement unit.
        state: Explicit measurement state.
        observed_at: Snapshot observation time.
        source_start: Inclusive source-range start.
        source_end: Inclusive source-range end.
        complete: Whether all required evidence is complete.
        confidence: Deterministic confidence within zero and one.
        data_health: Explicit upstream data-health state.
        evidence_refs: Bounded source evidence references.

    Returns:
        Validated detached JSON-safe mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails.
    """
    logger.info("Building IndicatorSnapshot v1")
    return _validated_mapping(
        {
            "schema": _SCHEMA,
            "indicator_id": indicator_id,
            "value": value,
            "unit": unit,
            "state": state,
            "observed_at": _utc_text(observed_at, "observed_at"),
            "source_start": _utc_text(source_start, "source_start"),
            "source_end": _utc_text(source_end, "source_end"),
            "complete": complete,
            "confidence": confidence,
            "data_health": data_health,
            "evidence_refs": list(evidence_refs),
        }
    )


@guard_public_boundary
def parse_indicator_snapshot(value: Mapping[str, object]) -> Mapping[str, Any]:
    """Parse and validate one IndicatorSnapshot v1 mapping.

    Args:
        value: Candidate JSON-safe mapping.

    Returns:
        Detached validated JSON-safe mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails.
    """
    logger.info("Parsing IndicatorSnapshot v1")
    return _validated_mapping(value)


_SCHEMA_V2 = "indicators.indicator_snapshot.v2"
_MAX_WARNINGS = 20
_MAX_INVALID_REASONS = 20
_MAX_COMPONENT_CONTRIBUTIONS = 64
_MAX_PARAMETERS = 64
_MAX_VALUES = 64

_PUBLICATION_STATES: frozenset[str] = frozenset(
    {
        "INVALID_FUTURE_INPUT",
        "INCOMPLETE_INPUT",
        "STALE_INPUT",
        "MISALIGNED_INPUT",
        "WARMING_UP",
        "DEPENDENCY_UNAVAILABLE",
        "VALID",
    }
)

_FIELDS_V2 = {
    "schema",
    "snapshot_id",
    "indicator_id",
    "indicator_version",
    "profile_id",
    "profile_version",
    "category",
    "symbol",
    "venue",
    "timeframe",
    "as_of",
    "available_at",
    "source_start",
    "source_end",
    "source_record_count",
    "source_dataset_id",
    "source_dataset_hash",
    "values",
    "units",
    "state",
    "completeness",
    "confidence",
    "data_health",
    "warmup_state",
    "parameters",
    "component_contributions",
    "warnings",
    "invalid_reasons",
    "provenance",
}

_CATEGORIES_V2: frozenset[str] = frozenset(
    {
        "market_speed",
        "market_regime",
        "trend",
        "structure",
        "liquidity",
        "order_flow",
        "volatility",
        "pattern",
    }
)

# ``VolatilitySnapshot`` per spec §14.2: the values mapping must carry at
# least ATR, ATR%, one selected realized/range estimator, the volatility
# percentile, the volatility z-score, and volatility-of-volatility.
_VOLATILITY_SNAPSHOT_REQUIRED_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "atr",
        "atr_percent",
        "realized_volatility",
        "volatility_percentile",
        "volatility_zscore",
        "volatility_of_volatility",
    }
)

# ``TrendSnapshot`` per spec §14.2: direction, strength, slopes, DMI/ADX,
# Aroon, and MACD/Supertrend values as requested. This domain's minimum
# required set covers direction/strength plus the ADX trio.
_TREND_SNAPSHOT_REQUIRED_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "direction",
        "strength",
        "adx",
        "plus_di",
        "minus_di",
    }
)

# ``StructureSnapshot`` per spec §14.2: active pivots, levels, clusters,
# gaps, and VWAP/profile references.
_STRUCTURE_SNAPSHOT_REQUIRED_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "pivot_high_price",
        "pivot_low_price",
        "donchian_upper",
        "donchian_lower",
        "anchored_vwap",
    }
)

# ``OrderFlowSnapshot`` per spec §14.2: OFI, book imbalance, CVD, aggressive
# imbalance, microprice proxy, and queue/sweep state. This domain currently
# only publishes CVD and aggressive-trade-imbalance (see
# ``order_flow/__init__.py`` for why OFI/book-imbalance/microprice/queue/
# sweep are unavailable); those five spec fields are represented as ``None``
# by the caller rather than fabricated, while ``cvd``/``aggressive_trade_imbalance``
# remain required.
_ORDER_FLOW_SNAPSHOT_REQUIRED_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "cvd",
        "aggressive_trade_imbalance",
    }
)

# ``MarketSpeedSnapshot`` per spec §14.2: price velocity, momentum
# acceleration, volume acceleration, and the composite gauge score. This
# domain currently does not publish order-flow velocity (see
# ``market_speed/__init__.py``), so it is represented as ``None`` by the
# caller rather than fabricated.
_MARKET_SPEED_SNAPSHOT_REQUIRED_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "price_velocity",
        "price_acceleration",
        "volume_acceleration",
        "composite_score",
    }
)

# ``MarketRegimeSnapshot`` per spec §14.2: the ADX/DMI, Choppiness, Donchian
# breakout, and stress regime candidates plus the resolved primary regime.
_MARKET_REGIME_SNAPSHOT_REQUIRED_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "adx_regime_candidate",
        "choppiness_state",
        "breakout_state",
        "stress_regime",
        "primary_regime",
    }
)

# ``PatternSnapshot`` per spec §14.2: at minimum the pattern's numeric
# publication state (see ``patterns/_shared.py`` for the domain's
# documented four-state simplification of the spec's five-state model).
_PATTERN_SNAPSHOT_REQUIRED_VALUE_KEYS: frozenset[str] = frozenset(
    {
        "pattern_state",
    }
)


def _validate_finite_number_mapping(
    mapping: Mapping[str, object], field: str, maximum_keys: int
) -> dict[str, float | None]:
    """Validate a bounded flat mapping of finite-or-null numeric values.

    Args:
        mapping: Candidate flat numeric mapping.
        field: Field name used in safe diagnostics.
        maximum_keys: Maximum approved key count.

    Returns:
        A detached mapping of ``float`` or ``None`` values.

    Raises:
        IndicatorError: If the mapping shape or any value is invalid.
    """
    if not isinstance(mapping, Mapping) or len(mapping) > maximum_keys:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot numeric mapping is invalid",
            {"field": field},
        )
    detached: dict[str, float | None] = {}
    for key, item in mapping.items():
        if not isinstance(key, str) or not key.strip():
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_SNAPSHOT,
                "snapshot numeric mapping key is invalid",
                {"field": field},
            )
        if item is None:
            detached[key] = None
            continue
        if (
            isinstance(item, bool)
            or not isinstance(item, int | float)
            or not math.isfinite(float(item))
        ):
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_SNAPSHOT,
                "snapshot numeric mapping value must be finite or null",
                {"field": field},
            )
        detached[key] = float(item)
    return detached


def _validate_string_list(value: object, field: str, maximum_items: int) -> list[str]:
    """Validate a bounded list of non-empty strings.

    Args:
        value: Candidate list.
        field: Field name used in safe diagnostics.
        maximum_items: Maximum approved item count.

    Returns:
        A detached list of strings.

    Raises:
        IndicatorError: If the shape or any item is invalid.
    """
    if (
        not isinstance(value, list | tuple)
        or len(value) > maximum_items
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "snapshot string list is invalid",
            {"field": field},
        )
    return list(value)


def _validated_mapping_v2(value: Mapping[str, object]) -> dict[str, Any]:
    """Validate and detach one v2 ``IndicatorSnapshot`` envelope mapping.

    Implements the spec §14.1 base envelope. This is additive to the v1
    transport (``_validated_mapping``): existing v1 producers/consumers are
    unaffected, and v1 is never deleted or mutated.

    Args:
        value: Candidate snapshot mapping.

    Returns:
        Detached validated JSON-safe mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails.
    """
    if set(value) != _FIELDS_V2 or value.get("schema") != _SCHEMA_V2:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot fields or schema are invalid",
        )
    for field in (
        "snapshot_id",
        "indicator_id",
        "indicator_version",
        "profile_id",
        "profile_version",
        "category",
        "symbol",
        "venue",
        "timeframe",
        "units",
        "state",
        "data_health",
        "warmup_state",
        "source_dataset_id",
        "source_dataset_hash",
    ):
        item = value[field]
        if not isinstance(item, str) or not item.strip():
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_SNAPSHOT,
                "v2 snapshot text field is invalid",
                {"field": field},
            )
    if value["category"] not in _CATEGORIES_V2:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot category is not one of the approved categories",
        )
    if value["state"] not in _PUBLICATION_STATES:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot state is not one of the approved publication states",
        )
    record_count = value["source_record_count"]
    if (
        isinstance(record_count, bool)
        or not isinstance(record_count, int)
        or record_count < 0
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot source_record_count must be a non-negative integer",
        )
    confidence = value["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, int | float)
        or not math.isfinite(float(confidence))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot confidence must be within zero and one",
        )
    completeness = value["completeness"]
    if (
        isinstance(completeness, bool)
        or not isinstance(completeness, int | float)
        or not math.isfinite(float(completeness))
        or not 0.0 <= float(completeness) <= 1.0
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot completeness must be within zero and one",
        )
    values = _validate_finite_number_mapping(
        cast("Mapping[str, object]", value["values"]),
        "values",
        _MAX_VALUES,
    )
    parameters_field = value["parameters"]
    if (
        not isinstance(parameters_field, Mapping)
        or len(parameters_field) > _MAX_PARAMETERS
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot parameters mapping is invalid",
        )
    component_contributions = _validate_finite_number_mapping(
        value["component_contributions"],  # type: ignore[arg-type]
        "component_contributions",
        _MAX_COMPONENT_CONTRIBUTIONS,
    )
    warnings = _validate_string_list(value["warnings"], "warnings", _MAX_WARNINGS)
    invalid_reasons = _validate_string_list(
        value["invalid_reasons"], "invalid_reasons", _MAX_INVALID_REASONS
    )
    provenance_field = value["provenance"]
    if not isinstance(provenance_field, Mapping):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "v2 snapshot provenance mapping is invalid",
        )
    as_of = _parse_utc(value["as_of"], "as_of")
    available = _parse_utc(value["available_at"], "available_at")
    source_start = _parse_utc(value["source_start"], "source_start")
    source_end = _parse_utc(value["source_end"], "source_end")
    if source_start > source_end or source_end > as_of or available < source_end:
        raise IndicatorError(
            IndicatorErrorCode.IND_LOOKAHEAD_RISK,
            "v2 snapshot source range is not causal",
        )
    detached = dict(value)
    detached["values"] = values
    detached["parameters"] = dict(parameters_field)
    detached["component_contributions"] = component_contributions
    detached["warnings"] = warnings
    detached["invalid_reasons"] = invalid_reasons
    detached["provenance"] = dict(provenance_field)
    detached["confidence"] = float(confidence)
    detached["completeness"] = float(completeness)
    canonical_json(detached, max_items=None)
    return detached


@guard_public_boundary
def build_indicator_snapshot_v2(
    *,
    snapshot_id: str,
    indicator_id: str,
    indicator_version: str,
    profile_id: str,
    profile_version: str,
    category: str,
    symbol: str,
    venue: str,
    timeframe: str,
    as_of: datetime,
    available_at: datetime,
    source_start: datetime,
    source_end: datetime,
    source_record_count: int,
    source_dataset_id: str,
    source_dataset_hash: str,
    values: Mapping[str, float | None],
    units: str,
    state: str,
    completeness: float,
    confidence: float,
    data_health: str,
    warmup_state: str,
    parameters: Mapping[str, object],
    component_contributions: Mapping[str, float | None] = MappingProxyType({}),
    warnings: Sequence[str] = (),
    invalid_reasons: Sequence[str] = (),
    provenance: Mapping[str, object] = MappingProxyType({}),
) -> Mapping[str, Any]:
    """Build one validated v2 ``IndicatorSnapshot`` envelope mapping.

    Implements the spec §14.1 base envelope shared by every category-
    specific snapshot type. This is additive alongside
    ``build_indicator_snapshot`` (v1): v1 producers/consumers are
    unaffected.

    Args:
        snapshot_id: Stable unique snapshot identifier.
        indicator_id: Stable official indicator identifier.
        indicator_version: Public implementation version.
        profile_id: Immutable indicator profile identifier.
        profile_version: Immutable indicator profile version.
        category: One of the nine spec ownership categories.
        symbol: Non-empty instrument symbol.
        venue: Non-empty venue identifier.
        timeframe: Non-empty source timeframe.
        as_of: The snapshot's decision-time instant.
        available_at: Earliest safe decision time for this snapshot.
        source_start: Inclusive source-range start.
        source_end: Inclusive source-range end.
        source_record_count: Non-negative source record count.
        source_dataset_id: Non-empty source dataset identifier.
        source_dataset_hash: Non-empty source dataset content hash.
        values: Bounded flat mapping of produced numeric values.
        units: Explicit measurement unit convention.
        state: One of the seven §14.3 publication states.
        completeness: Fraction of required evidence present, in ``[0, 1]``.
        confidence: Deterministic confidence within zero and one.
        data_health: Explicit upstream data-health state.
        warmup_state: Explicit warmup state description.
        parameters: Bounded flat mapping of the resolved profile parameters.
        component_contributions: Bounded flat mapping of named component
            contributions.
        warnings: Bounded list of non-fatal warning codes.
        invalid_reasons: Bounded list of invalidity reason codes.
        provenance: Bounded flat mapping of provenance evidence.

    Returns:
        Validated detached JSON-safe mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails.
    """
    logger.info("Building IndicatorSnapshot v2 for %s", indicator_id)
    return _validated_mapping_v2(
        {
            "schema": _SCHEMA_V2,
            "snapshot_id": snapshot_id,
            "indicator_id": indicator_id,
            "indicator_version": indicator_version,
            "profile_id": profile_id,
            "profile_version": profile_version,
            "category": category,
            "symbol": symbol,
            "venue": venue,
            "timeframe": timeframe,
            "as_of": _utc_text(as_of, "as_of"),
            "available_at": _utc_text(available_at, "available_at"),
            "source_start": _utc_text(source_start, "source_start"),
            "source_end": _utc_text(source_end, "source_end"),
            "source_record_count": source_record_count,
            "source_dataset_id": source_dataset_id,
            "source_dataset_hash": source_dataset_hash,
            "values": dict(values),
            "units": units,
            "state": state,
            "completeness": completeness,
            "confidence": confidence,
            "data_health": data_health,
            "warmup_state": warmup_state,
            "parameters": dict(parameters),
            "component_contributions": dict(component_contributions),
            "warnings": list(warnings),
            "invalid_reasons": list(invalid_reasons),
            "provenance": dict(provenance),
        }
    )


@guard_public_boundary
def parse_indicator_snapshot_v2(value: Mapping[str, object]) -> Mapping[str, Any]:
    """Parse and validate one v2 ``IndicatorSnapshot`` envelope mapping.

    Args:
        value: Candidate JSON-safe mapping.

    Returns:
        Detached validated JSON-safe mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails.
    """
    logger.info("Parsing IndicatorSnapshot v2")
    return _validated_mapping_v2(value)


@guard_public_boundary
def build_volatility_snapshot(
    *,
    snapshot_id: str,
    indicator_version: str,
    profile_id: str,
    profile_version: str,
    symbol: str,
    venue: str,
    timeframe: str,
    as_of: datetime,
    available_at: datetime,
    source_start: datetime,
    source_end: datetime,
    source_record_count: int,
    source_dataset_id: str,
    source_dataset_hash: str,
    values: Mapping[str, float | None],
    state: str,
    completeness: float,
    confidence: float,
    data_health: str,
    warmup_state: str,
    parameters: Mapping[str, object],
    component_contributions: Mapping[str, float | None] = MappingProxyType({}),
    warnings: Sequence[str] = (),
    invalid_reasons: Sequence[str] = (),
    provenance: Mapping[str, object] = MappingProxyType({}),
) -> Mapping[str, Any]:
    """Build one validated ``VolatilitySnapshot`` (spec §14.2 category row).

    ``VolatilitySnapshot`` is the first category-specific snapshot type
    built atop the shared v2 envelope. Its ``values`` mapping must carry at
    least ATR, ATR%, one selected realized/range estimator, the volatility
    percentile, the volatility z-score, and volatility-of-volatility.

    Args:
        snapshot_id: Stable unique snapshot identifier.
        indicator_version: Public implementation version.
        profile_id: Immutable indicator profile identifier.
        profile_version: Immutable indicator profile version.
        symbol: Non-empty instrument symbol.
        venue: Non-empty venue identifier.
        timeframe: Non-empty source timeframe.
        as_of: The snapshot's decision-time instant.
        available_at: Earliest safe decision time for this snapshot.
        source_start: Inclusive source-range start.
        source_end: Inclusive source-range end.
        source_record_count: Non-negative source record count.
        source_dataset_id: Non-empty source dataset identifier.
        source_dataset_hash: Non-empty source dataset content hash.
        values: Flat mapping of produced numeric values; must include the
            required ``VolatilitySnapshot`` keys.
        state: One of the seven §14.3 publication states.
        completeness: Fraction of required evidence present, in ``[0, 1]``.
        confidence: Deterministic confidence within zero and one.
        data_health: Explicit upstream data-health state.
        warmup_state: Explicit warmup state description.
        parameters: Bounded flat mapping of the resolved profile parameters.
        component_contributions: Bounded flat mapping of named component
            contributions.
        warnings: Bounded list of non-fatal warning codes.
        invalid_reasons: Bounded list of invalidity reason codes.
        provenance: Bounded flat mapping of provenance evidence.

    Returns:
        Validated detached JSON-safe ``VolatilitySnapshot`` mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails, including a
            missing required ``VolatilitySnapshot`` value key.
    """
    logger.info("Building VolatilitySnapshot for %s", symbol)
    missing = _VOLATILITY_SNAPSHOT_REQUIRED_VALUE_KEYS - set(values)
    if missing:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "VolatilitySnapshot is missing required value keys",
            {"keys": tuple(sorted(missing))},
        )
    return _validated_mapping_v2(
        {
            "schema": _SCHEMA_V2,
            "snapshot_id": snapshot_id,
            "indicator_id": "volatility_snapshot",
            "indicator_version": indicator_version,
            "profile_id": profile_id,
            "profile_version": profile_version,
            "category": "volatility",
            "symbol": symbol,
            "venue": venue,
            "timeframe": timeframe,
            "as_of": _utc_text(as_of, "as_of"),
            "available_at": _utc_text(available_at, "available_at"),
            "source_start": _utc_text(source_start, "source_start"),
            "source_end": _utc_text(source_end, "source_end"),
            "source_record_count": source_record_count,
            "source_dataset_id": source_dataset_id,
            "source_dataset_hash": source_dataset_hash,
            "values": dict(values),
            "units": "mixed",
            "state": state,
            "completeness": completeness,
            "confidence": confidence,
            "data_health": data_health,
            "warmup_state": warmup_state,
            "parameters": dict(parameters),
            "component_contributions": dict(component_contributions),
            "warnings": list(warnings),
            "invalid_reasons": list(invalid_reasons),
            "provenance": dict(provenance),
        }
    )


def _build_category_snapshot(
    *,
    indicator_id: str,
    category: str,
    required_keys: frozenset[str],
    snapshot_id: str,
    indicator_version: str,
    profile_id: str,
    profile_version: str,
    symbol: str,
    venue: str,
    timeframe: str,
    as_of: datetime,
    available_at: datetime,
    source_start: datetime,
    source_end: datetime,
    source_record_count: int,
    source_dataset_id: str,
    source_dataset_hash: str,
    values: Mapping[str, float | None],
    state: str,
    completeness: float,
    confidence: float,
    data_health: str,
    warmup_state: str,
    parameters: Mapping[str, object],
    component_contributions: Mapping[str, float | None],
    warnings: Sequence[str],
    invalid_reasons: Sequence[str],
    provenance: Mapping[str, object],
) -> dict[str, Any]:
    """Build one category-specific v2 snapshot shared by trend/structure/order_flow.

    Args:
        indicator_id: The category snapshot's fixed indicator identity.
        category: One of the nine spec ownership categories.
        required_keys: The category's minimum required ``values`` keys.
        snapshot_id: Stable unique snapshot identifier.
        indicator_version: Public implementation version.
        profile_id: Immutable indicator profile identifier.
        profile_version: Immutable indicator profile version.
        symbol: Non-empty instrument symbol.
        venue: Non-empty venue identifier.
        timeframe: Non-empty source timeframe.
        as_of: The snapshot's decision-time instant.
        available_at: Earliest safe decision time for this snapshot.
        source_start: Inclusive source-range start.
        source_end: Inclusive source-range end.
        source_record_count: Non-negative source record count.
        source_dataset_id: Non-empty source dataset identifier.
        source_dataset_hash: Non-empty source dataset content hash.
        values: Flat mapping of produced numeric values; must include the
            category's required keys.
        state: One of the seven §14.3 publication states.
        completeness: Fraction of required evidence present, in ``[0, 1]``.
        confidence: Deterministic confidence within zero and one.
        data_health: Explicit upstream data-health state.
        warmup_state: Explicit warmup state description.
        parameters: Bounded flat mapping of the resolved profile parameters.
        component_contributions: Bounded flat mapping of named component
            contributions.
        warnings: Bounded list of non-fatal warning codes.
        invalid_reasons: Bounded list of invalidity reason codes.
        provenance: Bounded flat mapping of provenance evidence.

    Returns:
        Validated detached JSON-safe category snapshot mapping.

    Raises:
        IndicatorError: If any snapshot invariant fails, including a
            missing required category value key.
    """
    missing = required_keys - set(values)
    if missing:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            f"{indicator_id} is missing required value keys",
            {"keys": tuple(sorted(missing))},
        )
    return _validated_mapping_v2(
        {
            "schema": _SCHEMA_V2,
            "snapshot_id": snapshot_id,
            "indicator_id": indicator_id,
            "indicator_version": indicator_version,
            "profile_id": profile_id,
            "profile_version": profile_version,
            "category": category,
            "symbol": symbol,
            "venue": venue,
            "timeframe": timeframe,
            "as_of": _utc_text(as_of, "as_of"),
            "available_at": _utc_text(available_at, "available_at"),
            "source_start": _utc_text(source_start, "source_start"),
            "source_end": _utc_text(source_end, "source_end"),
            "source_record_count": source_record_count,
            "source_dataset_id": source_dataset_id,
            "source_dataset_hash": source_dataset_hash,
            "values": dict(values),
            "units": "mixed",
            "state": state,
            "completeness": completeness,
            "confidence": confidence,
            "data_health": data_health,
            "warmup_state": warmup_state,
            "parameters": dict(parameters),
            "component_contributions": dict(component_contributions),
            "warnings": list(warnings),
            "invalid_reasons": list(invalid_reasons),
            "provenance": dict(provenance),
        }
    )


@guard_public_boundary
def build_trend_snapshot(
    *,
    snapshot_id: str,
    indicator_version: str,
    profile_id: str,
    profile_version: str,
    symbol: str,
    venue: str,
    timeframe: str,
    as_of: datetime,
    available_at: datetime,
    source_start: datetime,
    source_end: datetime,
    source_record_count: int,
    source_dataset_id: str,
    source_dataset_hash: str,
    values: Mapping[str, float | None],
    state: str,
    completeness: float,
    confidence: float,
    data_health: str,
    warmup_state: str,
    parameters: Mapping[str, object],
    component_contributions: Mapping[str, float | None] = MappingProxyType({}),
    warnings: Sequence[str] = (),
    invalid_reasons: Sequence[str] = (),
    provenance: Mapping[str, object] = MappingProxyType({}),
) -> Mapping[str, Any]:
    """Build one validated ``TrendSnapshot`` (spec §14.2 category row).

        Its ``values`` mapping must carry at least direction, strength, and the
        ADX/+DI/-DI trio; Aroon and MACD/Supertrend values may be included when
        requested but are not required.

    Args:
        snapshot_id: The snapshot id value.
        indicator_version: The indicator version value.
        profile_id: The profile id value.
        profile_version: The profile version value.
        symbol: The symbol value.
        venue: The venue value.
        timeframe: The timeframe value.
        as_of: The as of value.
        available_at: The available at value.
        source_start: The source start value.
        source_end: The source end value.
        source_record_count: The source record count value.
        source_dataset_id: The source dataset id value.
        source_dataset_hash: The source dataset hash value.
        values: The values value.
        state: The state value.
        completeness: The completeness value.
        confidence: The confidence value.
        data_health: The data health value.
        warmup_state: The warmup state value.
        parameters: The parameters value.
        component_contributions: The component contributions value.
        warnings: The warnings value.
        invalid_reasons: The invalid reasons value.
        provenance: The provenance value.

    Returns:
            Validated detached JSON-safe ``TrendSnapshot`` mapping.

    Raises:
            IndicatorError: If any snapshot invariant fails, including a
                missing required ``TrendSnapshot`` value key.
    """
    logger.info("Building TrendSnapshot for %s", symbol)
    return _build_category_snapshot(
        indicator_id="trend_snapshot",
        category="trend",
        required_keys=_TREND_SNAPSHOT_REQUIRED_VALUE_KEYS,
        snapshot_id=snapshot_id,
        indicator_version=indicator_version,
        profile_id=profile_id,
        profile_version=profile_version,
        symbol=symbol,
        venue=venue,
        timeframe=timeframe,
        as_of=as_of,
        available_at=available_at,
        source_start=source_start,
        source_end=source_end,
        source_record_count=source_record_count,
        source_dataset_id=source_dataset_id,
        source_dataset_hash=source_dataset_hash,
        values=values,
        state=state,
        completeness=completeness,
        confidence=confidence,
        data_health=data_health,
        warmup_state=warmup_state,
        parameters=parameters,
        component_contributions=component_contributions,
        warnings=warnings,
        invalid_reasons=invalid_reasons,
        provenance=provenance,
    )


@guard_public_boundary
def build_structure_snapshot(
    *,
    snapshot_id: str,
    indicator_version: str,
    profile_id: str,
    profile_version: str,
    symbol: str,
    venue: str,
    timeframe: str,
    as_of: datetime,
    available_at: datetime,
    source_start: datetime,
    source_end: datetime,
    source_record_count: int,
    source_dataset_id: str,
    source_dataset_hash: str,
    values: Mapping[str, float | None],
    state: str,
    completeness: float,
    confidence: float,
    data_health: str,
    warmup_state: str,
    parameters: Mapping[str, object],
    component_contributions: Mapping[str, float | None] = MappingProxyType({}),
    warnings: Sequence[str] = (),
    invalid_reasons: Sequence[str] = (),
    provenance: Mapping[str, object] = MappingProxyType({}),
) -> Mapping[str, Any]:
    """Build one validated ``StructureSnapshot`` (spec §14.2 category row).

        Its ``values`` mapping must carry at least the active pivot prices,
        Donchian bounds, and the anchored VWAP reference; level clusters, gaps,
        and volume-profile references may be included when requested.

    Args:
        snapshot_id: The snapshot id value.
        indicator_version: The indicator version value.
        profile_id: The profile id value.
        profile_version: The profile version value.
        symbol: The symbol value.
        venue: The venue value.
        timeframe: The timeframe value.
        as_of: The as of value.
        available_at: The available at value.
        source_start: The source start value.
        source_end: The source end value.
        source_record_count: The source record count value.
        source_dataset_id: The source dataset id value.
        source_dataset_hash: The source dataset hash value.
        values: The values value.
        state: The state value.
        completeness: The completeness value.
        confidence: The confidence value.
        data_health: The data health value.
        warmup_state: The warmup state value.
        parameters: The parameters value.
        component_contributions: The component contributions value.
        warnings: The warnings value.
        invalid_reasons: The invalid reasons value.
        provenance: The provenance value.

    Returns:
            Validated detached JSON-safe ``StructureSnapshot`` mapping.

    Raises:
            IndicatorError: If any snapshot invariant fails, including a
                missing required ``StructureSnapshot`` value key.
    """
    logger.info("Building StructureSnapshot for %s", symbol)
    return _build_category_snapshot(
        indicator_id="structure_snapshot",
        category="structure",
        required_keys=_STRUCTURE_SNAPSHOT_REQUIRED_VALUE_KEYS,
        snapshot_id=snapshot_id,
        indicator_version=indicator_version,
        profile_id=profile_id,
        profile_version=profile_version,
        symbol=symbol,
        venue=venue,
        timeframe=timeframe,
        as_of=as_of,
        available_at=available_at,
        source_start=source_start,
        source_end=source_end,
        source_record_count=source_record_count,
        source_dataset_id=source_dataset_id,
        source_dataset_hash=source_dataset_hash,
        values=values,
        state=state,
        completeness=completeness,
        confidence=confidence,
        data_health=data_health,
        warmup_state=warmup_state,
        parameters=parameters,
        component_contributions=component_contributions,
        warnings=warnings,
        invalid_reasons=invalid_reasons,
        provenance=provenance,
    )


@guard_public_boundary
def build_order_flow_snapshot(
    *,
    snapshot_id: str,
    indicator_version: str,
    profile_id: str,
    profile_version: str,
    symbol: str,
    venue: str,
    timeframe: str,
    as_of: datetime,
    available_at: datetime,
    source_start: datetime,
    source_end: datetime,
    source_record_count: int,
    source_dataset_id: str,
    source_dataset_hash: str,
    values: Mapping[str, float | None],
    state: str,
    completeness: float,
    confidence: float,
    data_health: str,
    warmup_state: str,
    parameters: Mapping[str, object],
    component_contributions: Mapping[str, float | None] = MappingProxyType({}),
    warnings: Sequence[str] = (),
    invalid_reasons: Sequence[str] = (),
    provenance: Mapping[str, object] = MappingProxyType({}),
) -> Mapping[str, Any]:
    """Build one validated ``OrderFlowSnapshot`` (spec §14.2 category row).

        Its ``values`` mapping must carry at least ``cvd`` and
        ``aggressive_trade_imbalance`` — the two spec ``IND-OF-*`` indicators
        this domain currently publishes. OFI, book imbalance, microprice,
        queue-depletion, and sweep-state values are not required (and should be
        passed as ``None``, never fabricated) because they need L2 book/trade-
        event input the current ``MarketDataset`` contract does not carry; see
        ``order_flow/__init__.py``.

    Args:
        snapshot_id: The snapshot id value.
        indicator_version: The indicator version value.
        profile_id: The profile id value.
        profile_version: The profile version value.
        symbol: The symbol value.
        venue: The venue value.
        timeframe: The timeframe value.
        as_of: The as of value.
        available_at: The available at value.
        source_start: The source start value.
        source_end: The source end value.
        source_record_count: The source record count value.
        source_dataset_id: The source dataset id value.
        source_dataset_hash: The source dataset hash value.
        values: The values value.
        state: The state value.
        completeness: The completeness value.
        confidence: The confidence value.
        data_health: The data health value.
        warmup_state: The warmup state value.
        parameters: The parameters value.
        component_contributions: The component contributions value.
        warnings: The warnings value.
        invalid_reasons: The invalid reasons value.
        provenance: The provenance value.

    Returns:
            Validated detached JSON-safe ``OrderFlowSnapshot`` mapping.

    Raises:
            IndicatorError: If any snapshot invariant fails, including a
                missing required ``OrderFlowSnapshot`` value key.
    """
    logger.info("Building OrderFlowSnapshot for %s", symbol)
    return _build_category_snapshot(
        indicator_id="order_flow_snapshot",
        category="order_flow",
        required_keys=_ORDER_FLOW_SNAPSHOT_REQUIRED_VALUE_KEYS,
        snapshot_id=snapshot_id,
        indicator_version=indicator_version,
        profile_id=profile_id,
        profile_version=profile_version,
        symbol=symbol,
        venue=venue,
        timeframe=timeframe,
        as_of=as_of,
        available_at=available_at,
        source_start=source_start,
        source_end=source_end,
        source_record_count=source_record_count,
        source_dataset_id=source_dataset_id,
        source_dataset_hash=source_dataset_hash,
        values=values,
        state=state,
        completeness=completeness,
        confidence=confidence,
        data_health=data_health,
        warmup_state=warmup_state,
        parameters=parameters,
        component_contributions=component_contributions,
        warnings=warnings,
        invalid_reasons=invalid_reasons,
        provenance=provenance,
    )


@guard_public_boundary
def evaluate_publication_state(
    *,
    any_source_after_as_of: bool,
    required_bar_not_closed: bool,
    required_source_stale: bool,
    timeframe_misaligned: bool,
    warmup_insufficient: bool,
    dependency_unavailable: bool,
) -> str:
    """Evaluate the spec §14.3 publication-validation state machine.

        Evaluates the seven declared conditions in their fixed priority order
        and returns the first state whose triggering condition is ``True``, or
        ``VALID`` if none trigger. A snapshot must never render an unknown
        value as zero or as the ``VALID`` state.

    Args:
            any_source_after_as_of: Whether any source ``available_at`` exceeds
                the candidate snapshot's ``as_of``.
            required_bar_not_closed: Whether a required bar is not closed.
            required_source_stale: Whether a required source exceeds the
                profile's maximum staleness age.
            timeframe_misaligned: Whether required timeframe alignment is not
                backward-only.
            warmup_insufficient: Whether the warm-up observation count is
                insufficient.
            dependency_unavailable: Whether a mandatory cross-category
                dependency is unavailable.

    Returns:
            One of the seven approved publication states, in priority order.

    Raises:
        None.
    """
    logger.info("Evaluating IndicatorSnapshot v2 publication state")
    if any_source_after_as_of:
        return "INVALID_FUTURE_INPUT"
    if required_bar_not_closed:
        return "INCOMPLETE_INPUT"
    if required_source_stale:
        return "STALE_INPUT"
    if timeframe_misaligned:
        return "MISALIGNED_INPUT"
    if warmup_insufficient:
        return "WARMING_UP"
    if dependency_unavailable:
        return "DEPENDENCY_UNAVAILABLE"
    return "VALID"


__all__ = [
    "build_indicator_snapshot",
    "build_indicator_snapshot_v2",
    "build_order_flow_snapshot",
    "build_structure_snapshot",
    "build_trend_snapshot",
    "build_volatility_snapshot",
    "evaluate_publication_state",
    "parse_indicator_snapshot",
    "parse_indicator_snapshot_v2",
]
