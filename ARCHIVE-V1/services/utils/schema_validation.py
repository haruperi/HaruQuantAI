"""Schema and payload validation tools for HaruQuant utilities."""

from __future__ import annotations

import time
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from app.services.utils.logger import logger
from app.services.utils.normalization import FixedClock, _evaluate_freshness
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

TOOL_CATEGORY = "utils"


def _validation_envelope(
    tool_name: str,
    *,
    valid: bool,
    errors: Iterable[str] = (),
    warnings: Iterable[str] = (),
    data: dict[str, Any] | None = None,
    request_id: str | None = None,
    started_at: float,
    error_code: str = "VALIDATION_FAILED",
) -> dict[str, Any]:
    """Build a bounded official validation envelope."""
    error_list = [str(item)[:500] for item in errors][:100]
    warning_list = [str(item)[:500] for item in warnings][:100]
    payload = dict(data or {})
    payload.update(
        {
            "valid": bool(valid),
            "validation_status": "success" if valid else "rejected",
            "errors": error_list,
            "warnings": warning_list,
            # Bounded list of offending fields. Kept in ``data`` so the
            # error payload stays exactly ``{code, details}`` per the
            # standard envelope contract.
            "invalid_fields": [] if valid else error_list[:10],
        }
    )
    res = standard_tool_response(
        ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY),
        "success" if valid else "error",
        "Validation passed." if valid else "Validation failed.",
        data=payload,
        error=(
            None
            if valid
            else {
                "code": error_code,
                "details": "; ".join(error_list)[:500] or "Validation failed.",
            }
        ),
        request_id=request_id,
        execution_ms=round((time.perf_counter() - started_at) * 1000, 3),
    )
    logger.info("Implemented validation envelope construction")
    return res


def validate_required_fields(
    *,
    payload: dict[str, Any],
    required_fields: list[str],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """Validate that required payload fields are present and non-empty."""
    del agent_name, environment
    started_at = time.perf_counter()
    if not isinstance(payload, dict):
        res = _validation_envelope(
            "validate_required_fields",
            valid=False,
            errors=["payload must be a dictionary"],
            request_id=request_id,
            started_at=started_at,
            error_code="INVALID_INPUT",
        )
        logger.info("Implemented validation of required fields")
        return res
    missing = [
        field
        for field in required_fields
        if payload.get(field) is None or payload.get(field) == ""
    ]
    res = _validation_envelope(
        "validate_required_fields",
        valid=not missing,
        errors=[f"missing required field: {field}" for field in missing],
        data={"missing_fields": missing},
        request_id=request_id,
        started_at=started_at,
    )
    logger.info("Implemented validation of required fields")
    return res


def _schema_type_ok(value: Any, expected: Any) -> bool:
    """Return whether a value matches a small JSON-schema type subset."""
    expected_values = expected if isinstance(expected, list) else [expected]
    for item in expected_values:
        if (item == "string" and isinstance(value, str)) or (
            item == "number"
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        ):
            res = True
            break
        if (
            (
                item == "integer"
                and isinstance(value, int)
                and not isinstance(value, bool)
            )
            or (item == "boolean" and isinstance(value, bool))
            or (item == "object" and isinstance(value, dict))
            or (item == "array" and isinstance(value, list))
            or (item == "null" and value is None)
        ):
            res = True
            break
    else:
        res = False
    logger.info("Implemented schema type check")
    return res


def _validate_schema_payload(
    payload: dict[str, Any],
    schema: dict[str, Any],
    expected_schema_version: str | None,
) -> tuple[list[str], list[str]]:
    """Validate a JSON-safe payload against the supported schema subset."""
    errors: list[str] = []
    warnings: list[str] = []
    required = list(schema.get("required", []))
    for field in required:
        if payload.get(field) is None or payload.get(field) == "":
            errors.append(f"{field} is required")

    expected_version = expected_schema_version or schema.get("schema_version")
    if expected_version is not None:
        actual = payload.get("schema_version")
        if actual is None:
            errors.append(
                f"schema_version is required and must equal {expected_version}"
            )
        elif str(actual) != str(expected_version):
            errors.append(
                f"schema_version mismatch: expected {expected_version}, got {actual}"
            )

    for field, spec in dict(schema.get("properties", {})).items():
        if field not in payload:
            continue
        expected_type = spec.get("type") if isinstance(spec, dict) else None
        if expected_type is not None and not _schema_type_ok(
            payload[field], expected_type
        ):
            errors.append(f"{field} must be {expected_type}")
        enum_values = spec.get("enum") if isinstance(spec, dict) else None
        if enum_values is not None and payload[field] not in enum_values:
            errors.append(f"{field} must be one of {list(enum_values)}")

    if len(payload) > 500:
        warnings.append(
            "payload field count exceeds MAX_FIELD_COUNT; diagnostics were bounded"
        )
    logger.debug("Implemented schema payload validation helper")
    return errors, warnings


def validate_input_schema(
    payload: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
    *,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    expected_schema_version: str | None = None,
) -> dict[str, Any]:
    """Validate an incoming JSON-safe payload against a schema subset."""
    del agent_name, environment
    started_at = time.perf_counter()
    if not isinstance(payload, dict) or not isinstance(schema, dict):
        res = _validation_envelope(
            "validate_input_schema",
            valid=False,
            errors=["payload and schema must be dictionaries"],
            request_id=request_id,
            started_at=started_at,
            error_code="INVALID_INPUT",
        )
        logger.info("Implemented validation of input schema")
        return res
    errors, warnings = _validate_schema_payload(
        payload, schema, expected_schema_version
    )
    res = _validation_envelope(
        "validate_input_schema",
        valid=not errors,
        errors=errors,
        warnings=warnings,
        data={"checked_fields": sorted(dict(schema.get("properties", {})))},
        request_id=request_id,
        started_at=started_at,
    )
    logger.info("Implemented validation of input schema")
    return res


def validate_output_schema(**kwargs: Any) -> dict[str, Any]:
    """Validate an outgoing JSON-safe payload against a schema subset."""
    result = validate_input_schema(**kwargs)
    result["metadata"]["tool_name"] = "validate_output_schema"
    logger.info("Implemented validation of output schema")
    return result


def validate_handoff_payload(
    *,
    handoff_payload: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    handoff_schema: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
    request_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate agent handoff payload shape."""
    active_payload = handoff_payload if handoff_payload is not None else payload
    active_schema = (
        handoff_schema
        or schema
        or {
            "required": ["source_agent", "target_agent", "payload"],
            "properties": {
                "source_agent": {"type": "string"},
                "target_agent": {"type": "string"},
                "payload": {"type": "object"},
            },
        }
    )
    result = validate_input_schema(
        payload=active_payload or {},
        schema=active_schema,
        request_id=request_id,
    )
    result["metadata"]["tool_name"] = "validate_handoff_payload"
    logger.info("Implemented agent handoff payload validation")
    return result


def validate_evidence_pack(
    *,
    evidence_pack: dict[str, Any],
    required_sections: list[str] | None = None,
    request_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate evidence-pack completeness."""
    result = validate_required_fields(
        payload=evidence_pack,
        required_fields=required_sections or ["summary", "evidence", "decision"],
        request_id=request_id,
    )
    result["metadata"]["tool_name"] = "validate_evidence_pack"
    logger.info("Implemented evidence-pack validation")
    return result


def validate_approval_packet(
    *,
    approval_packet: dict[str, Any],
    required_fields: list[str] | None = None,
    request_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate approval packet completeness."""
    result = validate_required_fields(
        payload=approval_packet,
        required_fields=required_fields or ["action", "reason", "requested_by"],
        request_id=request_id,
    )
    result["metadata"]["tool_name"] = "validate_approval_packet"
    logger.info("Implemented approval packet validation")
    return result


def validate_registry_entry(
    *,
    registry_entry: dict[str, Any],
    required_fields: list[str] | None = None,
    request_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate registry-entry completeness."""
    result = validate_required_fields(
        payload=registry_entry,
        required_fields=required_fields or ["name", "version", "owner"],
        request_id=request_id,
    )
    result["metadata"]["tool_name"] = "validate_registry_entry"
    logger.info("Implemented registry entry validation")
    return result


def validate_blocked_actions(
    *,
    attempted_actions: list[str],
    blocked_actions: list[str],
    request_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate that attempted actions do not include blocked actions."""
    started_at = time.perf_counter()
    blocked = sorted(set(attempted_actions) & set(blocked_actions))
    res = _validation_envelope(
        "validate_blocked_actions",
        valid=not blocked,
        errors=[f"blocked action attempted: {item}" for item in blocked],
        data={"blocked_actions": blocked},
        request_id=request_id,
        started_at=started_at,
        error_code="BLOCKED_ACTION",
    )
    logger.info("Implemented validation of blocked actions")
    return res


def validate_numeric_range(
    *,
    value: float,
    minimum: float | None = None,
    maximum: float | None = None,
    inclusive: bool = True,
    request_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate that a numeric value falls within optional bounds."""
    started_at = time.perf_counter()
    errors: list[str] = []
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append("value must be numeric")
    elif minimum is not None and (
        (inclusive and value < minimum) or (not inclusive and value <= minimum)
    ):
        errors.append(f"value must be {'>=' if inclusive else '>'} {minimum}")
    elif maximum is not None and (
        (inclusive and value > maximum) or (not inclusive and value >= maximum)
    ):
        errors.append(f"value must be {'<=' if inclusive else '<'} {maximum}")
    res = _validation_envelope(
        "validate_numeric_range",
        valid=not errors,
        errors=errors,
        data={
            "value": value,
            "minimum": minimum,
            "maximum": maximum,
            "inclusive": inclusive,
        },
        request_id=request_id,
        started_at=started_at,
    )
    logger.info("Implemented numeric range validation")
    return res


def validate_data_freshness(
    *,
    timestamp: Any = None,
    payload: dict[str, Any] | None = None,
    max_age_seconds: int = 30,
    now: Any = None,
    request_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Validate timestamp freshness with UTC-first semantics."""
    started_at = time.perf_counter()
    value = timestamp if timestamp is not None else (payload or {}).get("timestamp")
    try:
        current = now
        if current is not None and not isinstance(current, datetime):
            current = datetime.fromisoformat(str(current).replace("Z", "+00:00"))
        evaluated = _evaluate_freshness(
            value,
            max_age_seconds=max_age_seconds,
            clock=FixedClock(current or datetime.now(UTC)),
        )
        data = {
            "observed_at": evaluated.observed_at.isoformat(),
            "checked_at": evaluated.checked_at.isoformat(),
            "age_seconds": evaluated.age_seconds,
            "max_age_seconds": evaluated.max_age_seconds,
            "is_fresh": evaluated.is_fresh,
            "is_stale": not evaluated.is_fresh,
        }
        res = _validation_envelope(
            "validate_data_freshness",
            valid=bool(data["is_fresh"]),
            errors=(["timestamp is stale"] if not evaluated.is_fresh else []),
            data=data,
            request_id=request_id,
            started_at=started_at,
        )
        logger.info("Implemented validation of data freshness")
        return res
    except Exception as error:
        res = _validation_envelope(
            "validate_data_freshness",
            valid=False,
            errors=[str(error)],
            request_id=request_id,
            started_at=started_at,
            error_code="INVALID_INPUT",
        )
        logger.info("Implemented validation of data freshness")
        return res


__all__ = [
    "validate_approval_packet",
    "validate_blocked_actions",
    "validate_data_freshness",
    "validate_evidence_pack",
    "validate_handoff_payload",
    "validate_input_schema",
    "validate_numeric_range",
    "validate_output_schema",
    "validate_registry_entry",
    "validate_required_fields",
]
