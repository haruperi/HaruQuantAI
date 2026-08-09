"""Validated JSON-safe IndicatorSnapshot v1 transport."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)
from app.utils import canonical_json, get_logger

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


__all__ = ["build_indicator_snapshot", "parse_indicator_snapshot"]
