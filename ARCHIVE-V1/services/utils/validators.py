"""Shared schema and validation tools for all HaruQuant departments.

Purpose:
    This module provides generic validation helpers and comprehensive market
    data quality checks used across agent handoffs, approval packets,
    registry entries, and runtime environment checks.

Rule 1 - Entities:
    - DataQualityReport (Data Class): Comprehensive data quality report container.
    - DataSource (Protocol): Protocol for pluggable data sources.
    - OHLCVSchema (Data Class): Data class defining expected OHLCV column names.
    - validate_required_fields (AI Tool): Check for missing required fields in a payload.
    - validate_input_schema (AI Tool): Validate an incoming request payload against a schema.
    - validate_output_schema (AI Tool): Validate an outgoing response payload against a schema.
    - validate_evidence_pack (AI Tool): Validate the completeness of an evidence pack.
    - validate_handoff_payload (AI Tool): Validate agent-to-agent handoff structures.
    - validate_approval_packet (AI Tool): Validate approval request packets.
    - validate_environment_mode (AI Tool): Confirm runtime environment mode validity.
    - validate_data_freshness (AI Tool): Check whether timestamped data is stale.
    - validate_artifact_reference (AI Tool): Validate referenced artifact paths and existence.
    - validate_registry_entry (AI Tool): Validate agent/workflow registry records.
    - validate_blocked_actions (AI Tool): Confirm no forbidden actions were attempted.
    - prepare_ohlcv_data (Function): Prepare OHLCV data for validation, backtesting, or research.
    - get_session_ranges (Function): Filter bars belonging to a specific session.
    - compute_session_stats (Function): Compute per-session statistics (returns, range, vol).
    - validate_ohlcv_quality (Function): Run comprehensive OHLCV validation.
    - validate_price_sanity (Function): Validate OHLC price relationships.
    - validate_gaps (Function): Detect gaps in time series data.
    - validate_market_calendar_gaps (Function): Classify gaps using market-closed rules.
    - validate_numeric_integrity (Function): Detect non-numeric, missing, and infinite OHLCV values.
    - validate_timezone_awareness (Function): Check timezone awareness of datetime index.
    - validate_duplicate_ohlc_rows (Function): Detect identical OHLC rows.
    - validate_flatlines (Function): Detect stale repeated close prices.
    - validate_spikes (Function): Detect spikes and anomalies in price data.
    - validate_missing_timestamps (Function): Check for missing timestamps in time series data.
    - validate_zero_volume (Function): Detect bars with zero or very low volume.
    - validate_duplicates (Function): Detect duplicate timestamps in data.
    - validate_monotonic_timestamps (Function): Check that timestamps are monotonic non-decreasing.
    - validate_spread (Function): Analyze spread statistics.
    - validate_high_low (Function): Check that high is greater than or equal to low.
    - validate_negative_prices (Function): Check for negative prices.
    - validate_price_in_range (Function): Check that a price column is inside the [low, high] range.
    - validate_zero_prices (Function): Check for zero prices.
    - validate_find_column (Function): Return actual column name in df matching target case-insensitively.
    - validate_find_columns (Function): Find multiple columns by name case-insensitively.
    - validate_get_time_series (Function): Get the datetime series from a DataFrame index or time column.
    - validate_issue_severity (Function): Map issue to normalized severity.
    - validate_issue_remediation_action (Function): Map issue to recommended remediation action.
    - validate_annotate_issues (Function): Add severity and remediation metadata to issues.
    - validate_remediation_summary (Function): Build remediation summary from list of issues.

Notes:
    External-facing functions imported by app.services.utils are exposed through
    app/services/utils/__init__.py; private underscore helpers remain implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd

from app.services.utils.logger import logger
from app.services.utils.normalization import (
    FixedClock,
    _evaluate_freshness,
    _parse_datetime,
)
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = PROJECT_ROOT / "data" / "simulation_artifacts"
ENVIRONMENTS = {
    "local",
    "development",
    "dev",
    "test",
    "staging",
    "production",
    "paper",
    "live",
}
RISK_LEVELS = {"low", "medium", "high", "critical"}
SEVERITY_LEVELS = {"info", "low", "medium", "high", "critical"}
TIMEFRAME_FREQUENCIES: dict[str, str] = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min",
    "M30": "30min",
    "H1": "1h",
    "H4": "4h",
    "D1": "1D",
}
VALIDATION_PROFILES: dict[str, dict[str, Any]] = {
    "research": {
        "min_quality_score": 50.0,
        "max_medium_issue_ratio": 1.0,
        "min_coverage_ratio": 0.0,
        "allow_timezone_naive": True,
        "allow_zero_spread": True,
    },
    "backtest": {
        "min_quality_score": 80.0,
        "max_medium_issue_ratio": 0.2,
        "min_coverage_ratio": 0.95,
        "allow_timezone_naive": True,
        "allow_zero_spread": True,
    },
    "optimization": {
        "min_quality_score": 90.0,
        "max_medium_issue_ratio": 0.05,
        "min_coverage_ratio": 0.98,
        "allow_timezone_naive": False,
        "allow_zero_spread": False,
    },
    "live": {
        "min_quality_score": 95.0,
        "max_medium_issue_ratio": 0.01,
        "min_coverage_ratio": 0.99,
        "allow_timezone_naive": False,
        "allow_zero_spread": False,
    },
}


def _envelope(
    name: str,
    *,
    status: str = "success",
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Build a standard HaruQuant validation result envelope.

    Logic:
    1. Delegates to `tool_result_envelope` in `app.services.utils.common`.
    2. Logs the successful execution of the validation tool.

    Args:
        name (str): Name of the tool building the envelope.
        status (str): Execution status ('success', 'rejected', 'blocked').
        data (Dict, optional): The payload data.
        errors (List, optional): List of error messages.
        warnings (List, optional): List of warning messages.
        request_id (str, optional): Unique request identifier.
        agent_name (str, optional): Name of the calling agent.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    started_at = datetime.now(UTC)
    error_list = errors or []
    warning_list = warnings or []
    official_status = "success" if status == "success" and (not error_list) else "error"
    payload = dict(data or {})
    payload.update(
        {
            "valid": official_status == "success",
            "validation_status": status,
            "errors": error_list,
            "warnings": warning_list,
            "agent_name": agent_name,
            "environment": environment,
        }
    )
    execution_ms = round((datetime.now(UTC) - started_at).total_seconds() * 1000, 3)
    logger.info("Executed {} validation tool with status={}.", name, official_status)
    return standard_tool_response(
        ToolStandardSpec(tool_name=name, tool_category=TOOL_CATEGORY),
        official_status,
        "Validation passed." if official_status == "success" else "Validation failed.",
        data=payload,
        error=None
        if official_status == "success"
        else {
            "code": "BLOCKED_ACTION" if status == "blocked" else "VALIDATION_FAILED",
            "details": "; ".join(error_list) or "Validation failed.",
        },
        request_id=request_id,
        execution_ms=execution_ms,
    )


def _schema_version_errors(
    payload: dict[str, Any], schema: dict[str, Any], expected_schema_version: str | None
) -> list[str]:
    """Return schema-version mismatch errors for payload/schema contracts."""
    expected = expected_schema_version or schema.get("schema_version")
    if expected is None:
        logger.debug("Implemented schema version errors")
        return []
    actual = payload.get("schema_version")
    if actual is None:
        logger.debug("Implemented schema version errors")
        return [f"schema_version is required and must equal {expected}"]
    if str(actual) != str(expected):
        logger.debug("Implemented schema version errors")
        return [f"schema_version mismatch: expected {expected}, got {actual}"]
    logger.debug("Implemented schema version errors")
    return []


def _timeframe_to_frequency(value: str | None) -> str | None:
    """Translate a common market-data timeframe into a pandas frequency."""
    if value is None:
        logger.debug("Implemented timeframe to frequency")
        return None
    logger.debug("Implemented timeframe to frequency")
    return TIMEFRAME_FREQUENCIES.get(str(value).upper(), value)


def validate_required_fields(
    *,
    payload: dict[str, Any],
    required_fields: list[str],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Generic missing-input checker.

    This tool verifies that all specified keys are present and non-empty in
    the provided payload.

    Logic:
    1. Iterates through `required_fields`.
    2. Identifies keys missing from `payload` or having empty values.
    3. Returns a structured envelope indicating success or rejection.

    Args:
        payload (Dict[str, Any]): The dictionary to check.
        required_fields (List[str]): List of required keys.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    if not isinstance(payload, dict):
        logger.debug("Implemented validate required fields")
        return _envelope(
            "validate_required_fields",
            status="rejected",
            errors=["Payload must be a dictionary"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    missing = [
        field
        for field in required_fields
        if payload.get(field) is None or payload.get(field) == ""
    ]
    logger.debug("Implemented validate required fields")
    return _envelope(
        "validate_required_fields",
        status="rejected" if missing else "success",
        data={"valid": not missing, "missing_fields": missing},
        errors=[f"missing required fields: {missing}"] if missing else [],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def _validate_schema(
    name: str,
    payload: dict[str, Any],
    schema: dict[str, Any],
    request_id: str | None,
    agent_name: str | None,
    environment: str,
    expected_schema_version: str | None = None,
) -> dict[str, Any]:
    """
    Internal helper to validate a payload against a small JSON-schema subset.

    Logic:
    1. Checks for required fields using `validate_required_fields`.
    2. Iterates through properties defined in the schema.
    3. Validates the type of each present field against the expected type.
    4. Aggregates all errors and returns an envelope.

    Args:
        name (str): Name of the calling tool.
        payload (Dict): Payload to validate.
        schema (Dict): JSON-schema subset.
        request_id (str, optional): Request ID.
        agent_name (str, optional): Agent name.
        environment (str): Environment name.

    Returns:
        Dict[str, Any]: A validation envelope.
    """
    required = list(schema.get("required", []))
    result = validate_required_fields(
        payload=payload,
        required_fields=required,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )
    errors = list(result.get("data", {}).get("errors", []))
    errors.extend(_schema_version_errors(payload, schema, expected_schema_version))
    properties = schema.get("properties", {})
    for field, spec in properties.items():
        if field not in payload or "type" not in spec:
            continue
        expected = spec["type"]
        value = payload[field]
        type_ok = (
            (expected == "string" and isinstance(value, str))
            or (expected == "number" and isinstance(value, (int, float)))
            or (expected == "integer" and isinstance(value, int))
            or (expected == "boolean" and isinstance(value, bool))
            or (expected == "object" and isinstance(value, dict))
            or (expected == "array" and isinstance(value, list))
        )
        if not type_ok:
            errors.append(f"{field} must be {expected}")
    logger.debug("Implemented validate schema")
    return _envelope(
        name,
        status="rejected" if errors else "success",
        data={"valid": not errors, "checked_fields": sorted(properties)},
        errors=errors,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def validate_input_schema(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    expected_schema_version: str | None = None,
) -> dict[str, Any]:
    """
    Validate an incoming request payload against a schema.

    This tool checks for required fields and basic type constraints defined
    in the provided schema.

    Logic:
    1. Delegates validation logic to `_validate_schema`.
    2. Returns a structured envelope.

    Args:
        payload (Dict[str, Any]): The incoming request data.
        schema (Dict[str, Any]): JSON-schema subset for validation.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    if not isinstance(payload, dict) or not isinstance(schema, dict):
        logger.debug("Implemented validate input schema")
        return _envelope(
            "validate_input_schema",
            status="rejected",
            errors=["Payload and schema must be dictionaries"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    logger.debug("Implemented validate input schema")
    return _validate_schema(
        "validate_input_schema",
        payload,
        schema,
        request_id,
        agent_name,
        environment,
        expected_schema_version,
    )


def validate_output_schema(
    *,
    payload: dict[str, Any],
    schema: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    expected_schema_version: str | None = None,
) -> dict[str, Any]:
    """
    Validate an outgoing response payload against a schema.

    This tool ensures that the response being sent back follows the
    expected structure and types.

    Logic:
    1. Delegates validation logic to `_validate_schema`.
    2. Returns a structured envelope.

    Args:
        payload (Dict[str, Any]): The response data.
        schema (Dict[str, Any]): JSON-schema subset for validation.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    if not isinstance(payload, dict) or not isinstance(schema, dict):
        logger.debug("Implemented validate output schema")
        return _envelope(
            "validate_output_schema",
            status="rejected",
            errors=["Payload and schema must be dictionaries"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    logger.debug("Implemented validate output schema")
    return _validate_schema(
        "validate_output_schema",
        payload,
        schema,
        request_id,
        agent_name,
        environment,
        expected_schema_version,
    )


def validate_numeric_range(
    *,
    value: float,
    minimum: float | None = None,
    maximum: float | None = None,
    inclusive: bool = True,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Validate that a numeric value falls within an optional range.

    Args:
        value: Numeric value to validate.
        minimum: Optional lower bound.
        maximum: Optional upper bound.
        inclusive: Whether bounds are inclusive.
        request_id: Optional request ID.
        agent_name: Optional agent name.
        environment: Runtime environment.

    Returns:
        Standard validation envelope.
    """
    errors: list[str] = []
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append("value must be numeric")
    else:
        if minimum is not None:
            if inclusive and value < minimum:
                errors.append(f"value must be >= {minimum}")
            if not inclusive and value <= minimum:
                errors.append(f"value must be > {minimum}")
        if maximum is not None:
            if inclusive and value > maximum:
                errors.append(f"value must be <= {maximum}")
            if not inclusive and value >= maximum:
                errors.append(f"value must be < {maximum}")
    logger.debug("Implemented validate numeric range")
    return _envelope(
        "validate_numeric_range",
        status="rejected" if errors else "success",
        data={
            "value": value,
            "minimum": minimum,
            "maximum": maximum,
            "inclusive": inclusive,
        },
        errors=errors,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def validate_evidence_pack(
    *,
    evidence_pack: dict[str, Any],
    required_sections: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Validate the completeness of an evidence pack.

    Checks if the evidence pack contains the necessary sections for audit
    and decision-making (e.g., hypothesis, evidence, validation).

    Logic:
    1. Uses a default set of sections if none are provided.
    2. Calls `validate_required_fields` to check the presence of these sections.
    3. Overrides the `tool_name` in the result for clarity.

    Args:
        evidence_pack (Dict[str, Any]): The evidence pack to check.
        required_sections (List[str], optional): Custom list of sections.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    if not isinstance(evidence_pack, dict):
        logger.debug("Implemented validate evidence pack")
        return _envelope(
            "validate_evidence_pack",
            status="rejected",
            errors=["Evidence pack must be a dictionary"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    sections = required_sections or ["hypothesis", "evidence", "validation"]
    res = validate_required_fields(
        payload=evidence_pack,
        required_fields=sections,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )
    res["metadata"]["tool_name"] = "validate_evidence_pack"
    logger.debug("Implemented validate evidence pack")
    return res


def validate_handoff_payload(
    *,
    payload: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Validate agent-to-agent handoff structures.

    Ensures that a handoff request includes source/target agents,
    handoff type, and the core payload.

    Logic:
    1. Defines the set of required handoff fields.
    2. Calls `validate_required_fields` to verify their presence.
    3. Overrides the `tool_name` in the result.

    Args:
        payload (Dict[str, Any]): The handoff request data.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    if not isinstance(payload, dict):
        logger.debug("Implemented validate handoff payload")
        return _envelope(
            "validate_handoff_payload",
            status="rejected",
            errors=["Payload must be a dictionary"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    required = ["from_agent", "to_agent", "handoff_type", "payload"]
    res = validate_required_fields(
        payload=payload,
        required_fields=required,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )
    res["metadata"]["tool_name"] = "validate_handoff_payload"
    logger.debug("Implemented validate handoff payload")
    return res


def validate_approval_packet(
    *,
    packet: dict[str, Any],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Validate approval request packets.

    Ensures that an approval request includes action details, risk levels,
    and evidence for review.

    Logic:
    1. Defines required fields for an approval packet.
    2. Calls `validate_required_fields`.
    3. Overrides the `tool_name` in the result.

    Args:
        packet (Dict[str, Any]): The approval request data.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    if not isinstance(packet, dict):
        logger.debug("Implemented validate approval packet")
        return _envelope(
            "validate_approval_packet",
            status="rejected",
            errors=["Packet must be a dictionary"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    required = ["request_id", "action", "risk_level", "requested_by", "evidence"]
    res = validate_required_fields(
        payload=packet,
        required_fields=required,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )
    res["metadata"]["tool_name"] = "validate_approval_packet"
    logger.debug("Implemented validate approval packet")
    return res


def validate_environment_mode(
    *,
    mode: str,
    allowed_modes: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Confirm runtime environment mode validity.

    Validates that the current execution mode (e.g., 'paper', 'live') is
    within the allowed set for the requested operation.

    Logic:
    1. Uses a default set of environments if none are provided.
    2. Checks if the provided `mode` exists in the allowed set.
    3. Returns an envelope with `status="blocked"` if validation fails.

    Args:
        mode (str): The mode to validate.
        allowed_modes (List[str], optional): Custom list of allowed modes.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    allowed = set(allowed_modes or ENVIRONMENTS)
    ok = mode in allowed
    logger.debug("Implemented validate environment mode")
    return _envelope(
        "validate_environment_mode",
        status="success" if ok else "blocked",
        data={"valid": ok, "mode": mode, "allowed_modes": sorted(allowed)},
        errors=[] if ok else ["environment mode is not allowed"],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


def validate_data_freshness(
    *,
    observed_at: str,
    max_age_seconds: int,
    now: str | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Check whether evidence or timestamped data is stale.

    Evaluates the 'observed_at' timestamp against a TTL window.

    Logic:
    1. Parses the current time (or override `now`).
    2. Calls `evaluate_freshness` to compare the observation time with the check time.
    3. Returns a structured envelope with the freshness status and age metrics.

    Args:
        observed_at (str): ISO-8601 observation timestamp.
        max_age_seconds (int): Maximum allowed age in seconds.
        now (str, optional): Override current time for evaluation.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    try:
        current = _parse_datetime(now) if now else datetime.now(UTC)
        freshness = _evaluate_freshness(
            observed_at, max_age_seconds=max_age_seconds, clock=FixedClock(current)
        )
        return _envelope(
            "validate_data_freshness",
            status="success" if freshness.is_fresh else "rejected",
            data={
                "fresh": freshness.is_fresh,
                "age_seconds": freshness.age_seconds,
                "max_age_seconds": max_age_seconds,
            },
            errors=[] if freshness.is_fresh else ["data is stale"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    except Exception as error:
        logger.error(f"Freshness evaluation failed: {error}")
        return _envelope(
            "validate_data_freshness",
            status="rejected",
            errors=[f"Freshness evaluation failed: {error!s}"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )


def validate_artifact_reference(
    *,
    path: str,
    must_exist: bool = True,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Validate referenced artifact paths and existence.

    Checks if a file path is within the project root and optionally verifies
    its existence on disk.

    Logic:
    1. Resolves the provided `path` to an absolute path.
    2. Checks if the path is contained within the `PROJECT_ROOT`.
    3. Optionally verifies if the file exists on the filesystem.
    4. Returns a structured envelope with the results and any policy violations.

    Args:
        path (str): File path to validate.
        must_exist (bool): Whether to verify existence. Defaults to True.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    try:
        resolved = Path(path).resolve()
        inside_root = resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents
        exists = resolved.exists()
        errors = []
        if not inside_root:
            errors.append("artifact path must be inside project root")
        if must_exist and (not exists):
            errors.append("artifact does not exist")
        return _envelope(
            "validate_artifact_reference",
            status="rejected" if errors else "success",
            data={
                "path": str(resolved),
                "exists": exists,
                "inside_project_root": inside_root,
            },
            errors=errors,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    except Exception as error:
        logger.error(f"Artifact validation failed for {path}: {error}")
        return _envelope(
            "validate_artifact_reference",
            status="rejected",
            errors=[f"Artifact validation failed: {error!s}"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )


def validate_registry_entry(
    *,
    entry: dict[str, Any],
    required_fields: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Validate agent/workflow registry records.

    Ensures that a registry entry contains minimum required fields like
    ID, name, and status.

    Logic:
    1. Defines default required fields for registry entries.
    2. Calls `validate_required_fields` to verify their presence.
    3. Overrides the `tool_name` in the result.

    Args:
        entry (Dict[str, Any]): The registry record data.
        required_fields (List[str], optional): Custom list of required fields.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    if not isinstance(entry, dict):
        logger.debug("Implemented validate registry entry")
        return _envelope(
            "validate_registry_entry",
            status="rejected",
            errors=["Entry must be a dictionary"],
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
    fields = required_fields or ["id", "name", "status"]
    res = validate_required_fields(
        payload=entry,
        required_fields=fields,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )
    res["metadata"]["tool_name"] = "validate_registry_entry"
    logger.debug("Implemented validate registry entry")
    return res


def validate_blocked_actions(
    *,
    attempted_actions: list[str],
    blocked_actions: list[str],
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """
    Confirm no forbidden actions were attempted.

    Checks an agent's intended actions against a blocklist for the
    current security context.

    Logic:
    1. Calculates the intersection of attempted and blocked actions.
    2. Returns an envelope with `status="blocked"` if any intersections are found.

    Args:
        attempted_actions (List[str]): Actions the agent plans to take.
        blocked_actions (List[str]): Forbidden actions.
        request_id (str, optional): Unique request ID.
        agent_name (str, optional): Calling agent name.
        environment (str): Runtime environment.

    Returns:
        Dict[str, Any]: A structured validation envelope.
    """
    blocked = sorted(set(attempted_actions) & set(blocked_actions))
    logger.debug("Implemented validate blocked actions")
    return _envelope(
        "validate_blocked_actions",
        status="blocked" if blocked else "success",
        data={"blocked_attempts": blocked, "passed": not blocked},
        errors=["blocked actions attempted"] if blocked else [],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
    )


@dataclass
class DataQualityReport:
    """
    Comprehensive data quality report container.

    This dataclass captures metrics and issues found during market data
    validation, including a quality score and remediation advice.

    Args:
        timestamp (datetime): When the report was generated.
        total_rows (int): Number of rows analyzed.
        checks_performed (List[str]): Names of checks run.
        issues_found (List[Dict]): Detailed list of quality issues.
        summary (Dict): Aggregated metrics and status.
        quality_score (float): Quality percentage (0-100).
        is_valid (bool): Whether the data meets minimum quality standards.
        price_sanity_valid (bool): Success flag for price sanity checks.
        gaps_count (int): Number of time gaps detected.
        anomalies_count (int): Number of price spikes/anomalies detected.
        missing_timestamps_count (int): Number of missing bars in the sequence.
        zero_volume_count (int): Number of bars with no volume.
        duplicates_count (int): Number of bars with duplicate timestamps.
        spread_stats (Dict, optional): Statistics about bid-ask spreads.
        has_warnings (bool): Whether non-fatal warning-level issues were found.
        coverage_ratio (float, optional): Actual/expected data coverage ratio.
    """

    timestamp: datetime
    total_rows: int
    checks_performed: list[str]
    issues_found: list[dict[str, Any]]
    summary: dict[str, Any]
    quality_score: float
    is_valid: bool
    price_sanity_valid: bool = True
    gaps_count: int = 0
    anomalies_count: int = 0
    missing_timestamps_count: int = 0
    zero_volume_count: int = 0
    duplicates_count: int = 0
    spread_stats: dict[str, float] | None = None
    has_warnings: bool = False
    coverage_ratio: float | None = None

    def __str__(self) -> str:
        """
        Return a human-readable summary of the report.

        Logic: Formats the quality score, issue count, and validity status into a string.

        Returns:
            str: Human-readable summary.
        """
        logger.debug("Implemented str")
        return f"DataQualityReport(quality_score={self.quality_score:.1f}%, issues={len(self.issues_found)}, valid={self.is_valid})"

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the report to a JSON-serializable dictionary.

        Logic: Maps all dataclass fields to a dictionary, ensuring timestamps are stringified.

        Returns:
            Dict[str, Any]: Serialized report.
        """
        logger.debug("Implemented to dict")
        return {
            "timestamp": self.timestamp.isoformat()
            if hasattr(self.timestamp, "isoformat")
            else str(self.timestamp),
            "total_rows": self.total_rows,
            "checks_performed": self.checks_performed,
            "issues_found": self.issues_found,
            "summary": self.summary,
            "quality_score": self.quality_score,
            "is_valid": self.is_valid,
            "price_sanity_valid": self.price_sanity_valid,
            "gaps_count": self.gaps_count,
            "anomalies_count": self.anomalies_count,
            "missing_timestamps_count": self.missing_timestamps_count,
            "zero_volume_count": self.zero_volume_count,
            "duplicates_count": self.duplicates_count,
            "spread_stats": self.spread_stats,
            "has_warnings": self.has_warnings,
            "coverage_ratio": self.coverage_ratio,
        }


def validate_find_column(df: pd.DataFrame, target: str) -> str | None:
    """
    Return actual column name in df matching target case-insensitively.

    Logic:
    1. Iterates through all columns in the DataFrame.
    2. Compares the lowercase version of each column name with the lowercase target.
    3. Returns the first matching original column name or None.

    Args:
        df (pd.DataFrame): Input DataFrame.
        target (str): Target column name to search for.

    Returns:
        Optional[str]: Actual column name if found, otherwise None.
    """
    target_lower = target.lower()
    for col in df.columns:
        if str(col).lower() == target_lower:
            logger.debug("Implemented validate find column")
            return str(col)
    logger.debug("Implemented validate find column")
    return None


def validate_find_columns(df: pd.DataFrame, targets: list[str]) -> dict[str, str]:
    """
    Find multiple columns by name case-insensitively.

    Logic:
    1. Delegates to `validate_find_column` for each target.
    2. Builds a mapping from the requested name to the actual name in the DataFrame.

    Args:
        df (pd.DataFrame): Input DataFrame.
        targets (List[str]): List of target column names.

    Returns:
        Dict[str, str]: Mapping of requested names to actual column names.
    """
    mapping = {}
    for target in targets:
        found = validate_find_column(df, target)
        if found:
            mapping[target] = found
    logger.debug("Implemented validate find columns")
    return mapping


def validate_get_time_series(df: pd.DataFrame) -> pd.Series | None:
    """
    Get the datetime series from a DataFrame index or time column.

    Logic:
    1. Checks if the index is a `DatetimeIndex`.
    2. Searches for common time column names ("datetime", "time") case-insensitively.
    3. Returns the time series as a pandas Series or None.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        Optional[pd.Series]: Datetime series if found, otherwise None.
    """
    if isinstance(df.index, pd.DatetimeIndex):
        logger.debug("Implemented validate get time series")
        return df.index.to_series()
    time_col = validate_find_column(df, "datetime") or validate_find_column(df, "time")
    if time_col:
        logger.debug("Implemented validate get time series")
        return pd.to_datetime(df[time_col])
    logger.debug("Implemented validate get time series")
    return None


def _pandas() -> Any:
    """Return pandas lazily or raise a clear configuration error."""
    import importlib

    try:
        logger.debug("Implemented pandas")
        return importlib.import_module("pandas")
    except ImportError as exc:
        raise RuntimeError("pandas is required.") from exc


def prepare_ohlcv_data(
    df: pd.DataFrame, schema: Any | None = None, timestamp_column: str | None = None
) -> pd.DataFrame:
    """
    Prepare OHLCV data for validation, backtesting, or research.

    Logic:
    1. Standardizes column names to a canonical schema (Open, High, Low, Close, Volume, Spread).
    2. Ensures the DataFrame has a `DatetimeIndex`, attempting to convert columns like "time" or "date".
    3. Sorts the data by time.
    4. Adds default columns for Volume and Spread if they are missing.
    5. Returns a cleaned DataFrame containing the required columns and any extra data.

    Args:
        df (pd.DataFrame): Raw OHLCV DataFrame.
        schema (Any, optional): Custom schema mapping for column names.

    Returns:
        pd.DataFrame: Prepared DataFrame with DatetimeIndex and standard columns.

    Raises:
        ValueError: If a DatetimeIndex cannot be formed or required columns are missing.
    """
    pd = _pandas()
    if not isinstance(df, pd.DataFrame):
        from app.services.utils.errors import ValidationError

        raise ValidationError("df must be a pandas DataFrame.")
    df = df.copy()
    if schema is None:
        desired = {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "spread": "spread",
        }
        df.columns = [str(col).lower() for col in df.columns]
    else:
        desired = {
            "open": getattr(schema, "open", "Open"),
            "high": getattr(schema, "high", "High"),
            "low": getattr(schema, "low", "Low"),
            "close": getattr(schema, "close", "Close"),
            "volume": getattr(schema, "volume", "Volume"),
            "spread": getattr(schema, "spread", "Spread"),
        }
        rename_map: dict[Any, str] = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if col_lower == "open":
                rename_map[col] = desired["open"]
            elif col_lower == "high":
                rename_map[col] = desired["high"]
            elif col_lower == "low":
                rename_map[col] = desired["low"]
            elif col_lower == "close":
                rename_map[col] = desired["close"]
            elif col_lower in {"volume", "tick_volume", "tickvolume"}:
                rename_map[col] = desired["volume"]
            elif col_lower == "spread":
                rename_map[col] = desired["spread"]
        if rename_map:
            df = df.rename(columns=rename_map)

    def _is_dt_idx(idx: Any) -> bool:
        if isinstance(pd.DatetimeIndex, type):
            return isinstance(idx, pd.DatetimeIndex)
        return type(idx).__name__ in ("FakeIndex", "FakeDatetimeIndex", "DatetimeIndex")

    if timestamp_column:
        lower_columns = {str(col).lower(): col for col in df.columns}
        if timestamp_column.lower() not in lower_columns:
            from app.services.utils.errors import ValidationError

            raise ValidationError(f"timestamp column is missing: {timestamp_column}")
        actual_col = lower_columns[timestamp_column.lower()]
        df.index = pd.DatetimeIndex(df[actual_col])
        df = df.drop(columns=[actual_col])
        logger.debug(f"Converted '{actual_col}' column to DatetimeIndex")
    elif not _is_dt_idx(df.index):
        datetime_cols = ["time", "datetime", "timestamp", "date"]
        lower_columns = {str(col).lower(): col for col in df.columns}
        for col_name in datetime_cols:
            if col_name in lower_columns:
                actual_col = lower_columns[col_name]
                df.index = pd.DatetimeIndex(df[actual_col])
                df = df.drop(columns=[actual_col])
                logger.debug(f"Converted '{actual_col}' column to DatetimeIndex")
                break
    if not _is_dt_idx(df.index):
        raise ValueError(
            "Could not create DatetimeIndex. Data must have DatetimeIndex or one of: time, datetime, timestamp, date"
        )
    lower_columns = {str(col).lower(): col for col in df.columns}
    if desired["volume"] not in df.columns:
        df[desired["volume"]] = 0.0
        logger.debug("Added volume column with default value 0.0")
    if desired["spread"] not in df.columns:
        bid_col = lower_columns.get("bid")
        ask_col = lower_columns.get("ask")
        if bid_col in df.columns and ask_col in df.columns:
            df[desired["spread"]] = df[ask_col] - df[bid_col]
            logger.debug("Calculated spread from bid-ask")
        else:
            df[desired["spread"]] = 0.0
            logger.debug("Added spread column with default value 0.0")
    required = [
        desired["open"],
        desired["high"],
        desired["low"],
        desired["close"],
        desired["volume"],
        desired["spread"],
    ]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}\nAvailable columns: {list(df.columns)}"
        )
    df = df.sort_index()
    logger.info(f"Prepared OHLCV data with {len(df)} rows.")
    if schema is None:
        return df[required]
    extra_columns = [column for column in df.columns if column not in required]
    return df[required + extra_columns]


def validate_high_low(
    df: pd.DataFrame, high_col: str, low_col: str
) -> list[dict[str, Any]]:
    """
    Check that high is greater than or equal to low.

    Logic:
    1. Identifies rows where high < low.
    2. Annotates an internal `_price_valid` flag for the DataFrame.
    3. Returns a list of issue dictionaries containing affected indices.

    Args:
        df (pd.DataFrame): OHLCV DataFrame.
        high_col (str): Column name for high prices.
        low_col (str): Column name for low prices.

    Returns:
        List[Dict[str, Any]]: List of price sanity issues.
    """
    issues: list[dict[str, Any]] = []
    if high_col and low_col:
        invalid = df[high_col] < df[low_col]
        if invalid.any():
            count = invalid.sum()
            issues.append(
                {
                    "type": "price_sanity",
                    "check": "High >= Low",
                    "count": int(count),
                    "rows": df[invalid].index.tolist(),
                }
            )
            df.loc[invalid, "_price_valid"] = False
            logger.warning(f"Found {count} rows where High < Low")
    return issues


def validate_price_in_range(
    df: pd.DataFrame, price_col: str, low_col: str, high_col: str, check_name: str
) -> list[dict[str, Any]]:
    """
    Check that a price column is inside the [low, high] range.

    Logic:
    1. Identifies rows where the target price is outside the low/high bounds.
    2. Marks rows as invalid and records the violations.

    Args:
        df (pd.DataFrame): OHLCV DataFrame.
        price_col (str): The column to check (e.g., Open or Close).
        low_col (str): The floor price column.
        high_col (str): The ceiling price column.
        check_name (str): Label for the check.

    Returns:
        List[Dict[str, Any]]: List of price range issues.
    """
    issues: list[dict[str, Any]] = []
    if price_col and low_col and high_col:
        invalid = (df[price_col] < df[low_col]) | (df[price_col] > df[high_col])
        if invalid.any():
            count = invalid.sum()
            issues.append(
                {
                    "type": "price_sanity",
                    "check": check_name,
                    "count": int(count),
                    "rows": df[invalid].index.tolist(),
                }
            )
            df.loc[invalid, "_price_valid"] = False
            logger.warning(f"Found {count} rows where {check_name}")
    return issues


def validate_negative_prices(
    df: pd.DataFrame, price_cols: list[str]
) -> list[dict[str, Any]]:
    """
    Check for negative prices.

    Logic:
    1. Scans specified price columns for values < 0.
    2. Records violations for each column.

    Args:
        df (pd.DataFrame): OHLCV DataFrame.
        price_cols (List[str]): Columns to check for non-negativity.

    Returns:
        List[Dict[str, Any]]: List of negative price issues.
    """
    issues: list[dict[str, Any]] = []
    for col in price_cols:
        invalid = df[col] < 0
        if invalid.any():
            count = invalid.sum()
            issues.append(
                {
                    "type": "price_sanity",
                    "check": f"No negative prices ({col})",
                    "count": int(count),
                    "rows": df[invalid].index.tolist(),
                }
            )
            df.loc[invalid, "_price_valid"] = False
            logger.warning(f"Found {count} rows with negative prices in {col}")
    return issues


def validate_zero_prices(
    df: pd.DataFrame, price_cols: list[str]
) -> list[dict[str, Any]]:
    """
    Check for zero prices.

    Logic:
    1. Scans specified columns for values exactly equal to 0.
    2. Reports these as warnings as they are unusual but sometimes valid for some assets.

    Args:
        df (pd.DataFrame): OHLCV DataFrame.
        price_cols (List[str]): Columns to check for zeros.

    Returns:
        List[Dict[str, Any]]: List of zero price warnings.
    """
    issues: list[dict[str, Any]] = []
    for col in price_cols:
        invalid = df[col] == 0
        if invalid.any():
            count = invalid.sum()
            issues.append(
                {
                    "type": "price_sanity",
                    "check": f"No zero prices ({col})",
                    "count": int(count),
                    "rows": df[invalid].index.tolist(),
                    "severity": "warning",
                }
            )
            logger.warning(f"Found {count} rows with zero prices in {col}")
    return issues


def validate_price_sanity(
    data: pd.DataFrame, mark_invalid: bool = False
) -> tuple[bool, pd.DataFrame, list[dict[str, Any]]]:
    """
    Validate OHLC price relationships and non-negative prices.

    Logic:
    1. Finds canonical OHLC columns.
    2. Runs `validate_high_low` to ensure High >= Low.
    3. Runs `validate_price_in_range` for Open and Close relative to [Low, High].
    4. Runs `validate_negative_prices` and `validate_zero_prices`.
    5. Returns a boolean indicating aggregate success, the annotated DataFrame, and the issue list.

    Args:
        data (pd.DataFrame): Input OHLCV DataFrame.
        mark_invalid (bool): Whether to add an 'is_valid' column to the output.

    Returns:
        Tuple[bool, pd.DataFrame, List[Dict[str, Any]]]: (Success, DataFrame, Issues).
    """
    df = data.copy()
    issues: list[dict[str, Any]] = []
    ohlc_mapping = validate_find_columns(df, ["Open", "High", "Low", "Close"])
    if not ohlc_mapping:
        return (False, df, [{"type": "error", "message": "No OHLC columns found"}])
    open_col = ohlc_mapping.get("Open")
    high_col = ohlc_mapping.get("High")
    low_col = ohlc_mapping.get("Low")
    close_col = ohlc_mapping.get("Close")
    df["_price_valid"] = True
    if high_col and low_col:
        issues.extend(validate_high_low(df, high_col, low_col))
    if close_col and low_col and high_col:
        issues.extend(
            validate_price_in_range(
                df, close_col, low_col, high_col, "Close within [Low, High]"
            )
        )
    if open_col and low_col and high_col:
        issues.extend(
            validate_price_in_range(
                df, open_col, low_col, high_col, "Open within [Low, High]"
            )
        )
    price_cols = [c for c in [open_col, high_col, low_col, close_col] if c]
    issues.extend(validate_negative_prices(df, price_cols))
    issues.extend(validate_zero_prices(df, price_cols))
    all_valid = len(issues) == 0
    if mark_invalid:
        df["is_valid"] = df["_price_valid"]
    df = df.drop(columns=["_price_valid"], errors="ignore")
    logger.info(f"Price sanity check completed. Valid: {all_valid}")
    return (all_valid, df, issues)


def validate_gaps(
    data: pd.DataFrame,
    expected_frequency: str | timedelta | None = None,
    tolerance: float = 1.5,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Detect gaps in time series data.

    Logic:
    1. Identifies the datetime series.
    2. Calculates the difference between consecutive timestamps.
    3. Determines the `expected_diff` using the provided frequency or the mode of observed differences.
    4. Identifies gaps exceeding `expected_diff * tolerance`.
    5. Returns a DataFrame of gap start points and a detailed list of gap info.

    Args:
        data (pd.DataFrame): Time series DataFrame.
        expected_frequency (Union[str, timedelta], optional): Explicit expected bar frequency.
        tolerance (float): Multiplier for the frequency before a gap is flagged.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: (Gap Rows, Gap Info).
    """
    time_series = validate_get_time_series(data)
    if time_series is None:
        logger.error("Data must have a datetime index or time column for gap detection")
        return (pd.DataFrame(), [])
    time_df = pd.DataFrame({"Datetime": pd.to_datetime(time_series.values)})
    time_df = time_df.sort_values("Datetime")
    time_df["time_diff"] = time_df["Datetime"].diff()
    gap_info: list[dict[str, Any]] = []
    if expected_frequency:
        if isinstance(expected_frequency, str):
            expected_diff = pd.Timedelta(expected_frequency.replace("H", "h"))
        else:
            expected_diff = expected_frequency
    else:
        mode_diff = time_df["time_diff"].mode()
        expected_diff = (
            mode_diff.iloc[0] if len(mode_diff) > 0 else time_df["time_diff"].median()
        )
    threshold = expected_diff * tolerance
    gap_rows = time_df[time_df["time_diff"] > threshold]
    for _idx, row in gap_rows.iterrows():
        gap_duration = row["time_diff"]
        gap_info.append(
            {
                "type": "gap",
                "check": "time_gap",
                "count": max(int(gap_duration / expected_diff) - 1, 1),
                "gap_start": row["Datetime"] - gap_duration,
                "gap_end": row["Datetime"],
                "duration": gap_duration,
                "expected_periods": int(gap_duration / expected_diff),
                "actual_diff": gap_duration,
                "expected_diff": expected_diff,
            }
        )
    logger.info(f"Detected {len(gap_info)} gaps in data")
    return (gap_rows, gap_info)


def _is_market_closed_timestamp(point: pd.Timestamp, *, asset_class: str) -> bool:
    """Return whether a timestamp falls in a simple closed-market window."""
    asset = asset_class.lower()
    if asset in {"crypto", "digital_asset"}:
        logger.debug("Implemented is market closed timestamp")
        return False
    weekday = point.weekday()
    hour = point.hour
    if asset in {"fx", "forex", "cfd", "metal", "metals"}:
        logger.debug("Implemented is market closed timestamp")
        return bool(
            weekday == 5
            or (weekday == 4 and hour >= 22)
            or (weekday == 6 and hour < 22)
        )
    logger.debug("Implemented is market closed timestamp")
    return bool(weekday in {5, 6})


def _market_closed_points(
    start: pd.Timestamp,
    end: pd.Timestamp,
    frequency: pd.Timedelta,
    *,
    asset_class: str,
    broker_timezone: str | None,
) -> tuple[int, int]:
    """Count expected missing periods and market-closed periods between two timestamps."""
    if frequency <= pd.Timedelta(0):
        logger.debug("Implemented market closed points")
        return (0, 0)
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if broker_timezone:
        if start_ts.tzinfo is None:
            start_ts = start_ts.tz_localize(broker_timezone)
        else:
            start_ts = start_ts.tz_convert(broker_timezone)
        if end_ts.tzinfo is None:
            end_ts = end_ts.tz_localize(broker_timezone)
        else:
            end_ts = end_ts.tz_convert(broker_timezone)
    expected_points = pd.date_range(
        start=start_ts + frequency, end=end_ts - frequency, freq=frequency
    )
    if len(expected_points) == 0:
        logger.debug("Implemented market closed points")
        return (0, 0)
    closed = 0
    for point in expected_points:
        if _is_market_closed_timestamp(pd.Timestamp(point), asset_class=asset_class):
            closed += 1
    logger.debug("Implemented market closed points")
    return (len(expected_points), closed)


def _calendar_adjust_missing_timestamp_issue(
    missing_df: pd.DataFrame,
    issue: dict[str, Any],
    *,
    asset_class: str,
    broker_timezone: str | None,
) -> dict[str, Any]:
    """Adjust missing timestamp counts by excluding simple market-closed periods."""
    adjusted = dict(issue)
    if missing_df.empty or "MissingTimestamp" not in missing_df.columns:
        logger.debug("Implemented calendar adjust missing timestamp issue")
        return adjusted
    missing = pd.to_datetime(missing_df["MissingTimestamp"])
    if broker_timezone:
        if getattr(missing.dt, "tz", None) is None:
            missing = missing.dt.tz_localize(broker_timezone)
        else:
            missing = missing.dt.tz_convert(broker_timezone)
    closed_mask = missing.map(
        lambda value: _is_market_closed_timestamp(
            pd.Timestamp(value), asset_class=asset_class
        )
    )
    closed_count = int(closed_mask.sum())
    original_count = int(issue.get("count", len(missing)))
    actionable_count = max(original_count - closed_count, 0)
    adjusted["original_count"] = original_count
    adjusted["market_closed_timestamps_count"] = closed_count
    adjusted["count"] = actionable_count
    adjusted["calendar_adjusted"] = True
    if actionable_count == 0:
        adjusted["type"] = "market_closed_missing_timestamps"
        adjusted["check"] = "market_calendar_missing_timestamps"
    expected_total = max(int(issue.get("expected_total", 0)) - closed_count, 1)
    actual_total = int(issue.get("actual_total", 0))
    adjusted["calendar_adjusted_coverage"] = min(actual_total / expected_total, 1.0)
    logger.debug("Implemented calendar adjust missing timestamp issue")
    return adjusted


def validate_market_calendar_gaps(
    data: pd.DataFrame,
    expected_frequency: str | timedelta | None = None,
    tolerance: float = 1.5,
    *,
    symbol: str | None = None,
    asset_class: str = "fx",
    broker_timezone: str | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Detect gaps and classify market-closed gaps separately from actionable data gaps.

    Logic:
    1. Runs `validate_gaps` to identify timestamp gaps.
    2. Estimates missing periods inside each gap.
    3. Labels gaps dominated by closed-market periods as `market_closed_gap`.
    4. Returns the gap rows and classified issue list.

    Args:
        data (pd.DataFrame): Time series DataFrame.
        expected_frequency (Union[str, timedelta], optional): Explicit expected bar frequency.
        tolerance (float): Multiplier for the frequency before a gap is flagged.
        symbol (str, optional): Symbol being checked, used for reporting.
        asset_class (str): Asset class for simple market-closed rules.
        broker_timezone (str, optional): Timezone used to interpret session hours.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: Gap rows and classified gap issues.
    """
    gap_rows, gaps = validate_gaps(
        data, expected_frequency=expected_frequency, tolerance=tolerance
    )
    classified: list[dict[str, Any]] = []
    for gap in gaps:
        expected_diff = pd.Timedelta(gap["expected_diff"])
        total_periods, closed_periods = _market_closed_points(
            pd.Timestamp(gap["gap_start"]),
            pd.Timestamp(gap["gap_end"]),
            expected_diff,
            asset_class=asset_class,
            broker_timezone=broker_timezone,
        )
        issue = dict(gap)
        issue["symbol"] = symbol
        issue["asset_class"] = asset_class
        issue["market_closed_periods"] = closed_periods
        issue["actionable_missing_periods"] = max(
            _issue_affected_count(gap) - closed_periods, 0
        )
        if total_periods and closed_periods / total_periods >= 0.8:
            issue["type"] = "market_closed_gap"
            issue["check"] = "market_calendar_gap"
            issue["count"] = max(issue["actionable_missing_periods"], 1)
        classified.append(issue)
    market_closed = sum(
        1 for issue in classified if issue["type"] == "market_closed_gap"
    )
    logger.info(
        f"Market-calendar gap check completed with {len(classified)} gaps; {market_closed} classified as market-closed."
    )
    return (gap_rows, classified)


def validate_numeric_integrity(
    data: pd.DataFrame, columns: list[str] | None = None
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Validate numeric OHLCV values and coerce columns for downstream checks.

    Logic:
    1. Selects canonical OHLCVS columns unless explicit columns are provided.
    2. Coerces each selected column with pandas numeric conversion.
    3. Reports non-numeric, NaN/null, and infinite values by column.
    4. Returns a dataframe with numeric columns coerced.

    Args:
        data (pd.DataFrame): Input OHLCV dataframe.
        columns (List[str], optional): Specific columns to validate.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: Coerced dataframe and issues.
    """
    df = data.copy()
    if columns is None:
        mapping = validate_find_columns(
            df, ["Open", "High", "Low", "Close", "Volume", "Spread"]
        )
        columns = list(mapping.values())
    issues: list[dict[str, Any]] = []
    for col in columns:
        if col not in df.columns:
            continue
        original = df[col]
        coerced = pd.to_numeric(original, errors="coerce")
        non_null = original.notna()
        non_numeric = coerced.isna() & non_null
        nulls = original.isna()
        infinite = pd.Series(np.isinf(coerced), index=df.index).fillna(False)
        if non_numeric.any():
            bad_rows = df[non_numeric].index.tolist()
            issues.append(
                {
                    "type": "non_numeric",
                    "check": f"{col}_numeric",
                    "column": col,
                    "count": int(non_numeric.sum()),
                    "rows": bad_rows[:100],
                }
            )
        if nulls.any():
            bad_rows = df[nulls].index.tolist()
            issues.append(
                {
                    "type": "missing_values",
                    "check": f"{col}_not_null",
                    "column": col,
                    "count": int(nulls.sum()),
                    "rows": bad_rows[:100],
                }
            )
        if infinite.any():
            bad_rows = df[infinite].index.tolist()
            issues.append(
                {
                    "type": "infinite_values",
                    "check": f"{col}_finite",
                    "column": col,
                    "count": int(infinite.sum()),
                    "rows": bad_rows[:100],
                }
            )
        df[col] = coerced.replace([np.inf, -np.inf], np.nan)
    logger.info(f"Numeric integrity check completed with {len(issues)} issues.")
    return (df, issues)


def validate_timezone_awareness(data: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Check whether the dataframe uses a timezone-aware DatetimeIndex.

    Args:
        data (pd.DataFrame): Input OHLCV dataframe.

    Returns:
        List[Dict[str, Any]]: Timezone awareness issues.
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        logger.info(
            "Timezone awareness check skipped: data does not use a DatetimeIndex."
        )
        return []
    if data.index.tz is None:
        logger.info("Timezone awareness check completed with 1 issue.")
        return [
            {
                "type": "timezone",
                "check": "timezone_aware_index",
                "count": len(data),
                "message": "DatetimeIndex is timezone-naive; broker/session interpretation may be ambiguous.",
            }
        ]
    logger.info(f"Timezone awareness check completed. Timezone: {data.index.tz}.")
    return []


def validate_duplicate_ohlc_rows(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Detect repeated identical OHLC rows even when timestamps are unique.

    Args:
        data (pd.DataFrame): Input OHLCV dataframe.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: Duplicate rows and issues.
    """
    mapping = validate_find_columns(data, ["Open", "High", "Low", "Close"])
    cols = list(mapping.values())
    if len(cols) < 4:
        logger.info(
            "Duplicate OHLC row check skipped: required OHLC columns not found."
        )
        return (pd.DataFrame(), [])
    dupes = data[data[cols].duplicated(keep=False)]
    if dupes.empty:
        logger.info("Duplicate OHLC row check completed. Found 0 duplicate OHLC rows.")
        return (pd.DataFrame(), [])
    logger.warning(f"Duplicate OHLC row check detected {len(dupes)} duplicate rows.")
    return (
        dupes,
        [
            {
                "type": "duplicate_ohlc_rows",
                "check": "identical_ohlc_values",
                "count": len(dupes),
                "rows": dupes.index.tolist()[:100],
            }
        ],
    )


def validate_flatlines(
    data: pd.DataFrame, *, min_run_length: int = 10
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Detect stale price flatlines across consecutive close values.

    Args:
        data (pd.DataFrame): Input OHLCV dataframe.
        min_run_length (int): Minimum repeated close run length to flag.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: Flatline rows and issues.
    """
    close_col = validate_find_column(data, "close")
    if not close_col or len(data) < min_run_length:
        logger.info(
            "Flatline check skipped: close column missing or data shorter than threshold."
        )
        return (pd.DataFrame(), [])
    close = pd.to_numeric(data[close_col], errors="coerce")
    run_id = close.ne(close.shift()).cumsum()
    run_lengths = close.groupby(run_id).transform("size")
    mask = close.notna() & (run_lengths >= min_run_length)
    rows = data[mask]
    if rows.empty:
        logger.info("Flatline check completed. Found 0 stale close runs.")
        return (pd.DataFrame(), [])
    logger.warning(f"Flatline check detected {len(rows)} stale close rows.")
    return (
        rows,
        [
            {
                "type": "flatline",
                "check": "stale_close_run",
                "count": len(rows),
                "rows": rows.index.tolist()[:100],
                "min_run_length": min_run_length,
            }
        ],
    )


def validate_spikes(
    data: pd.DataFrame,
    columns: list[str] | None = None,
    method: str = "zscore",
    mark_anomalies: bool = True,
    z_score_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
    atr_window: int = 14,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Detect spikes and anomalies in market-derived series.

    Logic:
    1. Derives close returns, candle range percentage, open gaps, and ATR-normalized ranges.
    2. Uses Z-Score or IQR methods to identify outliers on those stationary-ish series.
    3. Falls back to explicitly provided raw columns when columns are supplied.
    4. Optionally marks anomalies in the returned DataFrame.

    Args:
        data (pd.DataFrame): Input DataFrame.
        columns (List[str], optional): Specific columns to check.
        method (str): Detection method ('zscore', 'iqr', or 'both').
        mark_anomalies (bool): Whether to add an 'is_anomaly' flag to the output.
        z_score_threshold (float): Threshold for Z-Score spikes.
        iqr_multiplier (float): Multiplier for IQR bounds.
        atr_window (int): Rolling window used for ATR-normalized anomaly bases.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: (Annotated DataFrame, Anomaly Info).
    """
    df = data.copy()
    anomalies: list[dict[str, Any]] = []
    derived_series: dict[str, pd.Series] = {}
    if columns is None:
        ohlc_mapping = validate_find_columns(df, ["Open", "High", "Low", "Close"])
        open_col = ohlc_mapping.get("Open")
        high_col = ohlc_mapping.get("High")
        low_col = ohlc_mapping.get("Low")
        close_col = ohlc_mapping.get("Close")
        if close_col:
            close = pd.to_numeric(df[close_col], errors="coerce")
            derived_series["close_return"] = close.pct_change()
            if open_col:
                open_price = pd.to_numeric(df[open_col], errors="coerce")
                derived_series["open_gap"] = (
                    open_price - close.shift(1)
                ) / close.shift(1)
        if high_col and low_col and close_col:
            high = pd.to_numeric(df[high_col], errors="coerce")
            low = pd.to_numeric(df[low_col], errors="coerce")
            close = pd.to_numeric(df[close_col], errors="coerce")
            derived_series["range_pct"] = (high - low) / close.replace(0, np.nan)
            prev_close = close.shift(1)
            true_range = pd.concat(
                [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
                axis=1,
            ).max(axis=1)
            atr = true_range.rolling(
                window=max(int(atr_window), 2), min_periods=max(2, int(atr_window) // 2)
            ).mean()
            derived_series["range_atr"] = true_range / atr.replace(0, np.nan)
            if open_col:
                open_price = pd.to_numeric(df[open_col], errors="coerce")
                derived_series["open_gap_atr"] = (
                    open_price - prev_close
                ).abs() / atr.replace(0, np.nan)
            spread_col = validate_find_column(df, "spread")
            if spread_col:
                spread = pd.to_numeric(df[spread_col], errors="coerce")
                derived_series["spread_atr"] = spread / atr.replace(0, np.nan)
        spread_col = validate_find_column(df, "spread")
        if spread_col:
            derived_series["spread_z"] = pd.to_numeric(df[spread_col], errors="coerce")
    else:
        for col in columns:
            if col in df.columns:
                derived_series[col] = pd.to_numeric(df[col], errors="coerce")
    if not derived_series:
        logger.warning("No columns found for spike detection")
        return (df, [])
    df["_is_anomaly"] = False
    for col, series in derived_series.items():
        col_data = series.replace([np.inf, -np.inf], np.nan).dropna()
        if method in ["zscore", "both"]:
            std = col_data.std()
            if std and (not pd.isna(std)):
                z_scores = np.abs((col_data - col_data.mean()) / std)
                z_anomalies = z_scores > z_score_threshold
                if z_anomalies.any():
                    anomaly_rows = col_data[z_anomalies].index.tolist()
                    anomalies.append(
                        {
                            "type": "spike",
                            "method": "zscore",
                            "check": col,
                            "count": len(anomaly_rows),
                            "rows": anomaly_rows,
                            "threshold": z_score_threshold,
                            "basis": "derived_market_series"
                            if columns is None
                            else "raw_column",
                        }
                    )
                    df.loc[anomaly_rows, "_is_anomaly"] = True
        if method in ["iqr", "both"]:
            Q1, Q3 = (col_data.quantile(0.25), col_data.quantile(0.75))
            IQR = Q3 - Q1
            lower_bound = Q1 - iqr_multiplier * IQR
            upper_bound = Q3 + iqr_multiplier * IQR
            iqr_anomalies = (col_data < lower_bound) | (col_data > upper_bound)
            if iqr_anomalies.any():
                anomaly_rows = col_data[iqr_anomalies].index.tolist()
                anomalies.append(
                    {
                        "type": "spike",
                        "method": "iqr",
                        "check": col,
                        "count": len(anomaly_rows),
                        "rows": anomaly_rows,
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "basis": "derived_market_series"
                        if columns is None
                        else "raw_column",
                    }
                )
                df.loc[anomaly_rows, "_is_anomaly"] = True
    if mark_anomalies:
        df["is_anomaly"] = df["_is_anomaly"]
    df = df.drop(columns=["_is_anomaly"], errors="ignore")
    logger.info(f"Spike detection completed. Found {len(anomalies)} anomalies.")
    return (df, anomalies)


def validate_missing_timestamps(
    data: pd.DataFrame,
    expected_frequency: str | timedelta | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Check for missing timestamps in time series data.

    Logic:
    1. Extracts timestamps from the DataFrame.
    2. Calculates the expected date range using the `start_date`, `end_date`, and `freq`.
    3. Finds the difference between the expected set and the actual set.
    4. Returns a DataFrame of missing timestamps and coverage metrics.

    Args:
        data (pd.DataFrame): Input time series.
        expected_frequency (Union[str, timedelta], optional): Expected bar interval.
        start_date (datetime, optional): Start of validation range.
        end_date (datetime, optional): End of validation range.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: (Missing Timestamps DF, Summary Info).
    """
    time_series = validate_get_time_series(data)
    if time_series is None:
        logger.error("Data must have a datetime index or time column")
        return (pd.DataFrame(), [])
    timestamps = pd.to_datetime(time_series.values)
    timestamps = pd.Series(timestamps).sort_values().unique()
    if start_date is None:
        start_date = (
            pd.Timestamp(timestamps[0]).to_pydatetime()
            if len(timestamps) > 0
            else datetime.now()
        )
    if end_date is None:
        end_date = (
            pd.Timestamp(timestamps[-1]).to_pydatetime()
            if len(timestamps) > 0
            else datetime.now()
        )
    if expected_frequency is None:
        diffs = pd.Series(timestamps).diff().dropna()
        if len(diffs) == 0:
            return (pd.DataFrame(), [])
        mode_diff = diffs.mode()
        expected_frequency = mode_diff.iloc[0] if len(mode_diff) > 0 else diffs.median()
    freq = pd.Timedelta(
        expected_frequency.replace("H", "h")
        if isinstance(expected_frequency, str)
        else expected_frequency
    )
    expected_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    missing_timestamps = sorted(set(expected_range) - set(timestamps))
    if missing_timestamps:
        missing_df = pd.DataFrame({"MissingTimestamp": missing_timestamps})
        missing_info = [
            {
                "type": "missing_timestamps",
                "count": len(missing_timestamps),
                "expected_total": len(expected_range),
                "actual_total": len(timestamps),
                "coverage": len(set(timestamps) & set(expected_range))
                / len(expected_range),
                "missing_timestamps": missing_timestamps[:100],
            }
        ]
        logger.warning(f"Detected {len(missing_timestamps)} missing timestamps.")
        return (missing_df, missing_info)
    logger.info("Missing timestamp check completed. Found 0 missing timestamps.")
    return (pd.DataFrame(), [])


def validate_zero_volume(
    data: pd.DataFrame, threshold: float = 0.0
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Detect bars with zero or very low volume.

    Logic:
    1. Locates the volume column.
    2. Identifies rows where volume is <= threshold.
    3. Records the count and positions of these rows.

    Args:
        data (pd.DataFrame): Input DataFrame.
        threshold (float): Volume threshold.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: (Zero Volume Rows, Issues).
    """
    volume_col = validate_find_column(data, "volume")
    if not volume_col:
        logger.info("Zero-volume check skipped: volume column not found.")
        return (pd.DataFrame(), [])
    zero_volume = data[data[volume_col] <= threshold]
    issues: list[dict[str, Any]] = []
    if len(zero_volume) > 0:
        issues.append(
            {
                "type": "zero_volume",
                "count": len(zero_volume),
                "rows": zero_volume.index.tolist(),
                "threshold": threshold,
            }
        )
        logger.info(f"Detected {len(zero_volume)} bars with zero volume.")
    else:
        logger.info("Zero-volume check completed. Found 0 zero-volume bars.")
    return (zero_volume, issues)


def validate_duplicates(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Detect duplicate timestamps in data.

    Logic:
    1. Checks for repeated timestamps in the index or time column.
    2. Returns the duplicated rows and a summary of unique repeated points.

    Args:
        data (pd.DataFrame): Input DataFrame.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: (Duplicate Rows, Issues).
    """
    time_series = validate_get_time_series(data)
    if time_series is None:
        logger.info("Duplicate timestamp check skipped: datetime series not found.")
        return (pd.DataFrame(), [])
    duplicates = time_series[time_series.duplicated(keep=False)]
    issues: list[dict[str, Any]] = []
    if len(duplicates) > 0:
        issues.append(
            {
                "type": "duplicates",
                "count": len(duplicates),
                "unique_timestamps": len(duplicates.unique()),
                "timestamps": duplicates.unique().tolist()[:100],
            }
        )
        logger.warning(f"Detected {len(duplicates)} duplicate timestamps.")
        return (data.loc[duplicates.index], issues)
    logger.info("Duplicate timestamp check completed. Found 0 duplicate timestamps.")
    return (pd.DataFrame(), [])


def validate_monotonic_timestamps(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Check that timestamps are monotonic non-decreasing.

    Logic:
    1. Verifies that every timestamp is greater than or equal to the previous one.
    2. Returns rows that appear "out of order" relative to their predecessor.

    Args:
        data (pd.DataFrame): Input DataFrame.

    Returns:
        Tuple[pd.DataFrame, List[Dict[str, Any]]]: (Disordered Rows, Issues).
    """
    time_series = validate_get_time_series(data)
    if time_series is None:
        logger.info("Monotonic timestamp check skipped: datetime series not found.")
        return (pd.DataFrame(), [])
    timestamps = pd.Series(pd.to_datetime(time_series.values))
    if len(timestamps) <= 1:
        logger.info("Monotonic timestamp check completed. Not enough rows to compare.")
        return (pd.DataFrame(), [])
    disorder_mask = timestamps < timestamps.shift(1)
    disorder_idx = disorder_mask[disorder_mask].index
    if len(disorder_idx) > 0:
        logger.warning(f"Detected {len(disorder_idx)} monotonic violations.")
        return (
            data.iloc[disorder_idx],
            [
                {
                    "type": "monotonic_timestamps",
                    "check": "timestamps_non_decreasing",
                    "count": int(len(disorder_idx)),
                    "positions": disorder_idx.astype(int).tolist()[:100],
                }
            ],
        )
    logger.info("Monotonic timestamp check completed. Found 0 ordering violations.")
    return (pd.DataFrame(), [])


def validate_spread(
    data: pd.DataFrame,
    *,
    max_allowed_spread: float | None = None,
    z_score_threshold: float = 4.0,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """
    Analyze spread statistics.

    Logic:
    1. Identifies spread or bid/ask columns.
    2. Calculates descriptive statistics for the spread.
    3. Adds percentile statistics and flags negative, zero, too-large, and z-score outlier spreads.

    Args:
        data (pd.DataFrame): Input DataFrame.
        max_allowed_spread (float, optional): Absolute spread ceiling to flag.
        z_score_threshold (float): Z-score threshold for spread outliers.

    Returns:
        Tuple[Dict[str, float], List[Dict[str, Any]]]: (Spread Stats, Spread Issues).
    """
    df = data.copy()
    spread_col = validate_find_column(df, "spread") or validate_find_column(df, "bid")
    if not spread_col:
        logger.info("Spread check skipped: no spread or bid column found.")
        return ({}, [])
    if spread_col == validate_find_column(df, "bid"):
        ask_col = validate_find_column(df, "ask")
        if ask_col:
            df["_spread"] = df[ask_col] - df[spread_col]
            spread_col = "_spread"
        else:
            logger.info("Spread check skipped: bid column found without ask column.")
            return ({}, [])
    spread_data = df[spread_col].dropna()
    if len(spread_data) == 0:
        logger.info(
            "Spread check completed. Spread column contained no non-null values."
        )
        return ({}, [])
    stats = {
        "mean": float(spread_data.mean()),
        "median": float(spread_data.median()),
        "std": float(spread_data.std()),
        "min": float(spread_data.min()),
        "max": float(spread_data.max()),
        "p90": float(spread_data.quantile(0.9)),
        "p95": float(spread_data.quantile(0.95)),
        "p99": float(spread_data.quantile(0.99)),
        "zero_count": int((spread_data == 0).sum()),
    }
    issues: list[dict[str, Any]] = []
    negative = spread_data[spread_data < 0]
    if len(negative) > 0:
        issues.append(
            {
                "type": "spread_anomaly",
                "issue": "negative_spread",
                "count": len(negative),
                "rows": negative.index.tolist(),
                "fatal": True,
            }
        )
        logger.warning(f"Detected {len(negative)} rows with negative spread.")
    zero = spread_data[spread_data == 0]
    if len(zero) > 0:
        issues.append(
            {
                "type": "spread_anomaly",
                "issue": "zero_spread",
                "count": len(zero),
                "rows": zero.index.tolist()[:100],
            }
        )
    if max_allowed_spread is not None:
        too_wide = spread_data[spread_data > max_allowed_spread]
        if len(too_wide) > 0:
            issues.append(
                {
                    "type": "spread_anomaly",
                    "issue": "max_allowed_spread",
                    "count": len(too_wide),
                    "rows": too_wide.index.tolist()[:100],
                    "max_allowed_spread": max_allowed_spread,
                }
            )
    std = spread_data.std()
    if std and (not pd.isna(std)):
        z_scores = np.abs((spread_data - spread_data.mean()) / std)
        outliers = spread_data[z_scores > z_score_threshold]
        if len(outliers) > 0:
            issues.append(
                {
                    "type": "spread_anomaly",
                    "issue": "spread_zscore_outlier",
                    "count": len(outliers),
                    "rows": outliers.index.tolist()[:100],
                    "threshold": z_score_threshold,
                }
            )
    logger.info(f"Spread check completed with {len(issues)} issues.")
    return (stats, issues)


def validate_issue_severity(issue: dict[str, Any]) -> str:
    """
    Map issue to normalized severity.

    Logic:
    1. Returns "high" for structural or critical price errors.
    2. Returns "medium" for continuity or liquidity issues.
    3. Returns "low" for warnings.

    Args:
        issue (Dict[str, Any]): Issue dictionary.

    Returns:
        str: Severity level ('high', 'medium', 'low').
    """
    issue_type = str(issue.get("type", "")).lower()
    issue_name = str(issue.get("issue", "")).lower()
    if bool(issue.get("fatal")):
        logger.debug("Implemented validate issue severity")
        return "critical"
    if issue_type in {
        "schema_validation",
        "monotonic_timestamps",
        "duplicates",
        "price_sanity",
        "non_numeric",
        "missing_values",
        "infinite_values",
        "minimum_history",
    }:
        logger.debug("Implemented validate issue severity")
        return "high"
    if issue_type == "spread_anomaly" and issue_name == "negative_spread":
        logger.debug("Implemented validate issue severity")
        return "critical"
    if issue_type in {"gap", "missing_timestamps", "zero_volume", "spread_anomaly"}:
        logger.debug("Implemented validate issue severity")
        return "medium"
    if issue_type in {
        "timezone",
        "duplicate_ohlc_rows",
        "flatline",
        "market_closed_gap",
        "market_closed_missing_timestamps",
    }:
        logger.debug("Implemented validate issue severity")
        return "low"
    logger.debug("Implemented validate issue severity")
    return "low"


def validate_issue_remediation_action(issue: dict[str, Any]) -> str:
    """
    Map issue to recommended remediation action.

    Logic: Looks up the issue type in a predefined action mapping.

    Args:
        issue (Dict[str, Any]): Issue dictionary.

    Returns:
        str: Remediation action name.
    """
    issue_type = str(issue.get("type", "")).lower()
    mapping = {
        "schema_validation": "normalize_schema",
        "monotonic_timestamps": "sort_by_timestamp",
        "duplicates": "deduplicate_timestamps",
        "gap": "backfill_or_drop",
        "missing_timestamps": "backfill_or_drop",
        "spike": "review_or_filter",
        "zero_volume": "drop_zero_volume",
        "price_sanity": "drop_invalid_ohlc",
        "non_numeric": "coerce_or_drop_invalid_values",
        "missing_values": "backfill_or_drop",
        "infinite_values": "drop_or_replace_infinite_values",
        "spread_anomaly": "review_spread_source_or_filter",
        "timezone": "localize_or_convert_timezone",
        "duplicate_ohlc_rows": "review_vendor_duplication",
        "flatline": "review_feed_staleness",
        "minimum_history": "extend_history_window",
        "market_closed_gap": "ignore_market_closed_gap",
        "market_closed_missing_timestamps": "ignore_market_closed_periods",
    }
    logger.debug("Implemented validate issue remediation action")
    return mapping.get(issue_type, "review_manually")


def validate_annotate_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Add severity and remediation metadata.

    Logic: Mutates each issue in the list to include severity and remediation hints.

    Args:
        issues (List[Dict[str, Any]]): List of raw issues.

    Returns:
        List[Dict[str, Any]]: Annotated issues.
    """
    for issue in issues:
        issue["severity"] = validate_issue_severity(issue)
        issue["remediation_action"] = validate_issue_remediation_action(issue)
        issue["remediation_required"] = issue["severity"] in {"critical", "high"}
    logger.info(f"Annotated {len(issues)} validation issues with severity metadata.")
    return issues


def validate_remediation_summary(issues: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build remediation summary.

    Logic: Aggregates counts of issues by severity and determines if immediate action is needed.

    Args:
        issues (List[Dict[str, Any]]): Annotated issue list.

    Returns:
        Dict[str, Any]: Remediation summary report.
    """
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for issue in issues:
        severity = issue.get("severity", "low")
        if severity in counts:
            counts[severity] += 1
    logger.info(f"Built remediation summary for {len(issues)} validation issues.")
    return {
        "severity_counts": counts,
        "needs_immediate_action": counts["critical"] > 0 or counts["high"] > 0,
    }


def _issue_affected_count(issue: dict[str, Any]) -> int:
    """Return the best available affected-row count for an issue."""
    if "count" in issue:
        try:
            logger.debug("Implemented issue affected count")
            return max(int(issue["count"]), 1)
        except (TypeError, ValueError):
            return 1
    for key in ("rows", "positions", "timestamps", "missing_timestamps"):
        value = issue.get(key)
        if isinstance(value, list):
            logger.debug("Implemented issue affected count")
            return max(len(value), 1)
    logger.debug("Implemented issue affected count")
    return 1


def _quality_score_from_issues(issues: list[dict[str, Any]], total_rows: int) -> float:
    """Calculate a severity and affected-row weighted quality score."""
    if any(issue.get("fatal") for issue in issues):
        logger.debug("Implemented quality score from issues")
        return 0.0
    severity_weights = {"critical": 100.0, "high": 60.0, "medium": 25.0, "low": 10.0}
    denominator = max(int(total_rows), 1)
    penalty = 0.0
    for issue in issues:
        severity = str(issue.get("severity", "low")).lower()
        weight = severity_weights.get(severity, 10.0)
        affected_ratio = min(_issue_affected_count(issue) / denominator, 1.0)
        penalty += weight * affected_ratio
    logger.debug("Implemented quality score from issues")
    return round(max(0.0, 100.0 - min(penalty, 100.0)), 4)


def _quality_penalty_breakdown(
    issues: list[dict[str, Any]], total_rows: int
) -> dict[str, Any]:
    """Build issue-level and grouped penalty details for quality score explanation."""
    severity_weights = {"critical": 100.0, "high": 60.0, "medium": 25.0, "low": 10.0}
    denominator = max(int(total_rows), 1)
    details: list[dict[str, Any]] = []
    by_type: dict[str, dict[str, Any]] = {}
    by_severity: dict[str, dict[str, Any]] = {}
    fatal = any(issue.get("fatal") for issue in issues)
    for issue in issues:
        issue_type = str(issue.get("type", "unknown"))
        severity = str(issue.get("severity", "low")).lower()
        affected_count = _issue_affected_count(issue)
        affected_ratio = min(affected_count / denominator, 1.0)
        severity_weight = severity_weights.get(severity, 10.0)
        penalty_points = severity_weight * affected_ratio
        detail = {
            "type": issue_type,
            "check": issue.get("check") or issue.get("issue") or issue_type,
            "severity": severity,
            "affected_count": affected_count,
            "affected_ratio": round(affected_ratio, 8),
            "severity_weight": severity_weight,
            "penalty_points": round(penalty_points, 4),
        }
        details.append(detail)
        type_bucket = by_type.setdefault(
            issue_type,
            {
                "issues": 0,
                "affected_count": 0,
                "penalty_points": 0.0,
                "max_severity": severity,
            },
        )
        type_bucket["issues"] += 1
        type_bucket["affected_count"] += affected_count
        type_bucket["penalty_points"] += penalty_points
        if severity_weights.get(severity, 0) > severity_weights.get(
            type_bucket["max_severity"], 0
        ):
            type_bucket["max_severity"] = severity
        severity_bucket = by_severity.setdefault(
            severity, {"issues": 0, "affected_count": 0, "penalty_points": 0.0}
        )
        severity_bucket["issues"] += 1
        severity_bucket["affected_count"] += affected_count
        severity_bucket["penalty_points"] += penalty_points
    total_penalty = (
        100.0 if fatal else min(sum(item["penalty_points"] for item in details), 100.0)
    )
    for group in (by_type, by_severity):
        for values in group.values():
            values["affected_ratio"] = round(values["affected_count"] / denominator, 8)
            values["penalty_points"] = round(values["penalty_points"], 4)
    logger.debug("Implemented quality penalty breakdown")
    return {
        "base_score": 100.0,
        "total_rows": denominator,
        "fatal": fatal,
        "total_penalty_points": round(total_penalty, 4),
        "score_after_penalty": round(max(0.0, 100.0 - total_penalty), 4),
        "by_type": by_type,
        "by_severity": by_severity,
        "details": details,
    }


def _issue_count_by_type(issues: list[dict[str, Any]], issue_type: str) -> int:
    """Aggregate affected counts for one issue type."""
    logger.debug("Implemented issue count by type")
    return sum(
        _issue_affected_count(issue)
        for issue in issues
        if str(issue.get("type", "")).lower() == issue_type
    )


def _detect_synthetic_ohlcvs_columns(
    raw: pd.DataFrame, prepared: pd.DataFrame
) -> list[str]:
    """Identify canonical columns created during OHLCV preparation."""
    raw_columns = {str(col).strip().lower() for col in raw.columns}
    prepared_columns = {str(col).strip().lower() for col in prepared.columns}
    synthetic: list[str] = []
    if "volume" in prepared_columns and (
        not raw_columns & {"volume", "vol", "tick_volume", "tickvolume", "real_volume"}
    ):
        synthetic.append("volume")
    if "spread" in prepared_columns and (
        not ("spread" in raw_columns or {"bid", "ask"} <= raw_columns)
    ):
        synthetic.append("spread")
    logger.debug("Implemented detect synthetic ohlcvs columns")
    return synthetic


def _validate_symbol_consistency(
    data: pd.DataFrame, expected_symbol: str | None
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate symbol consistency when an expected symbol is supplied."""
    if not expected_symbol:
        logger.debug("Implemented validate symbol consistency")
        return ({"status": "not_requested", "expected_symbol": None}, [])
    symbol_col = validate_find_column(data, "symbol")
    if symbol_col is None:
        logger.debug("Implemented validate symbol consistency")
        return (
            {
                "status": "unavailable",
                "expected_symbol": expected_symbol,
                "symbol_column": None,
            },
            [],
        )
    values = sorted(
        str(value).upper() for value in data[symbol_col].dropna().unique().tolist()
    )
    expected = expected_symbol.upper()
    mismatches = [value for value in values if value != expected]
    issues: list[dict[str, Any]] = []
    if mismatches:
        issues.append(
            {
                "type": "symbol_mismatch",
                "check": "symbol_consistency",
                "count": len(mismatches),
                "expected_symbol": expected_symbol,
                "observed_symbols": values[:10],
            }
        )
    logger.debug("Implemented validate symbol consistency")
    return (
        {
            "status": "verified" if not mismatches else "mismatch",
            "expected_symbol": expected_symbol,
            "symbol_column": symbol_col,
            "observed_symbols": values[:10],
            "mismatch_count": len(mismatches),
        },
        issues,
    )


def _profile_settings(profile: str, overrides: dict[str, Any]) -> dict[str, Any]:
    """Return validation profile settings with caller overrides applied."""
    settings = dict(VALIDATION_PROFILES.get(profile, VALIDATION_PROFILES["research"]))
    for key in (
        "min_quality_score",
        "max_medium_issue_ratio",
        "min_coverage_ratio",
        "allow_timezone_naive",
        "allow_zero_spread",
    ):
        if key in overrides and overrides[key] is not None:
            settings[key] = overrides[key]
    logger.debug("Implemented profile settings")
    return settings


def _build_quality_decision(
    results: dict[str, Any], profile: str, settings: dict[str, Any]
) -> dict[str, Any]:
    """Build profile-aware admission guidance from validation results."""
    summary = results["summary"]
    issues = results["issues_found"]
    total_rows = max(int(results.get("total_rows") or 0), 1)
    quality_score = float(summary.get("quality_score", 0.0))
    coverage_ratio = float(summary.get("coverage", {}).get("coverage_ratio", 1.0))
    medium_affected = sum(
        _issue_affected_count(issue)
        for issue in issues
        if issue.get("severity") == "medium"
    )
    medium_issue_ratio = min(medium_affected / total_rows, 1.0)
    reasons: list[str] = []
    if not summary.get("is_valid", False):
        reasons.append("critical_or_high_severity_issue")
    if quality_score < float(settings["min_quality_score"]):
        reasons.append("quality_score_below_profile_threshold")
    if coverage_ratio < float(settings["min_coverage_ratio"]):
        reasons.append("coverage_below_profile_threshold")
    if medium_issue_ratio > float(settings["max_medium_issue_ratio"]):
        reasons.append("medium_issue_ratio_above_profile_threshold")
    if not bool(settings["allow_timezone_naive"]) and any(
        issue.get("type") == "timezone" for issue in issues
    ):
        reasons.append("timezone_naive_not_allowed")
    if not bool(settings["allow_zero_spread"]) and any(
        issue.get("type") == "spread_anomaly" and issue.get("issue") == "zero_spread"
        for issue in issues
    ):
        reasons.append("zero_spread_not_allowed")
    if reasons:
        admission = "fail"
        recommended_action = (
            "reject" if not summary.get("is_valid", False) else "repair_then_use"
        )
    elif summary.get("has_warnings"):
        admission = "pass_with_warnings"
        recommended_action = "use"
    else:
        admission = "pass"
        recommended_action = "use"
    suitable_for: dict[str, bool] = {}
    for candidate, base_settings in VALIDATION_PROFILES.items():
        candidate_decision = _build_quality_decision_simple(
            issues, summary, total_rows, base_settings
        )
        suitable_for[candidate] = candidate_decision
    logger.debug("Implemented build quality decision")
    return {
        "profile": profile,
        "profile_settings": settings,
        "admission": admission,
        "recommended_action": recommended_action,
        "reasons": reasons,
        "metrics": {
            "quality_score": quality_score,
            "coverage_ratio": coverage_ratio,
            "medium_issue_ratio": round(medium_issue_ratio, 8),
        },
        "suitable_for": suitable_for,
    }


def _build_quality_decision_simple(
    issues: list[dict[str, Any]],
    summary: dict[str, Any],
    total_rows: int,
    settings: dict[str, Any],
) -> bool:
    """Return a boolean suitability decision for one profile."""
    quality_score = float(summary.get("quality_score", 0.0))
    coverage_ratio = float(summary.get("coverage", {}).get("coverage_ratio", 1.0))
    medium_affected = sum(
        _issue_affected_count(issue)
        for issue in issues
        if issue.get("severity") == "medium"
    )
    logger.debug("Implemented build quality decision simple")
    return (
        bool(summary.get("is_valid", False))
        and quality_score >= float(settings["min_quality_score"])
        and (coverage_ratio >= float(settings["min_coverage_ratio"]))
        and (
            medium_affected / max(total_rows, 1)
            <= float(settings["max_medium_issue_ratio"])
        )
        and (
            bool(settings["allow_timezone_naive"])
            or not any(issue.get("type") == "timezone" for issue in issues)
        )
        and (
            bool(settings["allow_zero_spread"])
            or not any(
                issue.get("type") == "spread_anomaly"
                and issue.get("issue") == "zero_spread"
                for issue in issues
            )
        )
    )


def _validate_ohlcv_quality_engine(
    data: pd.DataFrame,
    checks: list[str] | None = None,
    return_report: bool = False,
    *,
    profile: str = "research",
    z_score_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
    atr_window: int = 14,
    **kwargs: Any,
) -> dict[str, Any] | DataQualityReport:
    """
    Run comprehensive OHLCV data validation.

    Logic:
    1. Executes a suite of data quality checks (monotonicity, schema, sanity, gaps, spikes, etc.).
    2. Aggregates results into a single issues list.
    3. Annotates issues with severity and remediation actions.
    4. Calculates an overall quality score.
    5. Returns a structured result dictionary or a `DataQualityReport` object.

    Args:
        data (pd.DataFrame): OHLCV DataFrame.
        checks (List[str], optional): List of checks to perform.
        return_report (bool): If True, returns a `DataQualityReport` object.
        profile (str): Validation profile for the decision block.
        z_score_threshold (float): Z-score for spike detection.
        iqr_multiplier (float): IQR multiplier for spike detection.
        atr_window (int): Rolling window used by ATR-normalized spike checks.

    Returns:
        Union[Dict, DataQualityReport]: Validation results.
    """
    profile = profile.lower()
    if profile not in VALIDATION_PROFILES:
        logger.warning(
            f"Unknown validation profile '{profile}', falling back to research."
        )
        profile = "research"
    decision_settings = _profile_settings(profile, kwargs)
    if checks is None:
        checks = [
            "monotonic_timestamps",
            "normalized_schema",
            "numeric_integrity",
            "timezone",
            "price_sanity",
            "gaps",
            "spikes",
            "missing_timestamps",
            "zero_volume",
            "duplicates",
            "duplicate_ohlc_rows",
            "flatlines",
            "spread",
        ]
    expected_frequency = kwargs.get("expected_frequency") or _timeframe_to_frequency(
        kwargs.get("timeframe")
    )
    raw_input = data
    raw_total_rows = len(data)
    results: dict[str, Any] = {
        "timestamp": datetime.now(),
        "total_rows": raw_total_rows,
        "checks_performed": [],
        "issues_found": [],
        "summary": {},
    }
    if "monotonic_timestamps" in checks:
        _, issues = validate_monotonic_timestamps(data)
        results["checks_performed"].append("monotonic_timestamps")
        results["issues_found"].extend(issues)
    schema_ok = True
    if "normalized_schema" in checks:
        results["checks_performed"].append("normalized_schema")
        try:
            prepared = prepare_ohlcv_data(data)
            synthetic_columns = _detect_synthetic_ohlcvs_columns(data, prepared)
            sorted_changed = False
            original_time = validate_get_time_series(data)
            if original_time is not None:
                original_values = pd.to_datetime(original_time.values)
                sorted_changed = not pd.Index(original_values).equals(prepared.index)
            data = prepared
            results["total_rows"] = len(data)
            results["summary"]["normalized_schema"] = {
                "valid": True,
                "columns": list(data.columns),
                "rows": len(data),
                "sorted_index": data.index.is_monotonic_increasing,
                "sorting_changed_order": sorted_changed,
                "duplicate_index_count": int(data.index.duplicated(keep=False).sum()),
                "synthetic_columns": synthetic_columns,
            }
        except Exception as e:
            schema_ok = False
            results["issues_found"].append(
                {
                    "type": "schema_validation",
                    "check": "prepare_data",
                    "count": max(raw_total_rows, 1),
                    "message": str(e),
                    "fatal": True,
                }
            )
            results["summary"]["normalized_schema"] = {
                "valid": False,
                "message": str(e),
            }
    if not schema_ok:
        results["issues_found"] = validate_annotate_issues(results["issues_found"])
        results["summary"]["remediation"] = validate_remediation_summary(
            results["issues_found"]
        )
        results["summary"]["total_issues"] = len(results["issues_found"])
        results["summary"]["quality_penalty_breakdown"] = _quality_penalty_breakdown(
            results["issues_found"], max(raw_total_rows, 1)
        )
        results["summary"]["quality_score"] = _quality_score_from_issues(
            results["issues_found"], max(raw_total_rows, 1)
        )
        results["summary"]["is_valid"] = False
        results["summary"]["has_warnings"] = False
        results["decision"] = _build_quality_decision(
            results, profile, decision_settings
        )
        logger.warning(
            "OHLCV quality check stopped after fatal schema validation failure."
        )
        if return_report:
            return DataQualityReport(
                timestamp=results["timestamp"],
                total_rows=raw_total_rows,
                checks_performed=results["checks_performed"],
                issues_found=results["issues_found"],
                summary=results["summary"],
                quality_score=results["summary"]["quality_score"],
                is_valid=False,
                has_warnings=False,
            )
        return results
    if "numeric_integrity" in checks:
        data, issues = validate_numeric_integrity(data)
        results["checks_performed"].append("numeric_integrity")
        results["issues_found"].extend(issues)
        results["summary"]["numeric_integrity"] = {
            "issues_count": len(issues),
            "affected_rows": sum(_issue_affected_count(issue) for issue in issues),
        }
    if "timezone" in checks:
        issues = validate_timezone_awareness(data)
        results["checks_performed"].append("timezone")
        results["issues_found"].extend(issues)
        results["summary"]["timezone"] = {
            "timezone": str(data.index.tz)
            if isinstance(data.index, pd.DatetimeIndex)
            else None,
            "is_timezone_aware": isinstance(data.index, pd.DatetimeIndex)
            and data.index.tz is not None,
        }
    if "price_sanity" in checks:
        all_valid, _, issues = validate_price_sanity(data)
        results["checks_performed"].append("price_sanity")
        results["issues_found"].extend(issues)
        results["summary"]["price_sanity"] = {
            "all_valid": all_valid,
            "issues_count": len(issues),
            "affected_rows": sum(_issue_affected_count(issue) for issue in issues),
        }
    if "gaps" in checks:
        if bool(kwargs.get("calendar_aware_gaps", True)):
            _, gaps = validate_market_calendar_gaps(
                data,
                expected_frequency=expected_frequency,
                tolerance=float(kwargs.get("gap_tolerance", 1.5)),
                symbol=kwargs.get("symbol"),
                asset_class=str(kwargs.get("asset_class", "fx")),
                broker_timezone=kwargs.get("broker_timezone"),
            )
        else:
            _, gaps = validate_gaps(
                data,
                expected_frequency=expected_frequency,
                tolerance=float(kwargs.get("gap_tolerance", 1.5)),
            )
        results["checks_performed"].append("gaps")
        results["issues_found"].extend(gaps)
        actionable = [
            issue for issue in gaps if issue.get("type") != "market_closed_gap"
        ]
        market_closed = [
            issue for issue in gaps if issue.get("type") == "market_closed_gap"
        ]
        results["summary"]["gaps"] = {
            "gap_events": len(gaps),
            "actionable_gap_events": len(actionable),
            "market_closed_gap_events": len(market_closed),
            "estimated_missing_periods": sum(
                _issue_affected_count(issue) for issue in gaps
            ),
            "actionable_missing_periods": sum(
                int(
                    issue.get(
                        "actionable_missing_periods", _issue_affected_count(issue)
                    )
                )
                for issue in gaps
            ),
        }
    if "spikes" in checks:
        _, anomalies = validate_spikes(
            data,
            z_score_threshold=z_score_threshold,
            iqr_multiplier=iqr_multiplier,
            atr_window=atr_window,
        )
        results["checks_performed"].append("spikes")
        results["issues_found"].extend(anomalies)
        results["summary"]["spikes"] = {
            "issues_count": len(anomalies),
            "affected_rows": sum(_issue_affected_count(issue) for issue in anomalies),
        }
    if "missing_timestamps" in checks:
        missing_df, info = validate_missing_timestamps(
            data, expected_frequency=expected_frequency
        )
        if info and bool(kwargs.get("calendar_aware_missing_timestamps", True)):
            info = [
                _calendar_adjust_missing_timestamp_issue(
                    missing_df,
                    issue,
                    asset_class=str(kwargs.get("asset_class", "fx")),
                    broker_timezone=kwargs.get("broker_timezone"),
                )
                for issue in info
            ]
        results["checks_performed"].append("missing_timestamps")
        results["issues_found"].extend(info)
        coverage_value = (
            info[0].get("calendar_adjusted_coverage") or info[0].get("coverage")
            if info
            else 1.0
        )
        results["summary"]["coverage"] = {
            "coverage_ratio": float(
                coverage_value if coverage_value is not None else 1.0
            ),
            "missing_timestamps_count": sum(
                _issue_affected_count(issue) for issue in info
            ),
            "market_closed_timestamps_count": sum(
                int(issue.get("market_closed_timestamps_count", 0)) for issue in info
            ),
            "calendar_adjusted": bool(info and info[0].get("calendar_adjusted")),
        }
    if "zero_volume" in checks:
        _, issues = validate_zero_volume(data)
        results["checks_performed"].append("zero_volume")
        results["issues_found"].extend(issues)
        results["summary"]["zero_volume"] = {
            "affected_rows": sum(_issue_affected_count(issue) for issue in issues)
        }
    if "duplicates" in checks:
        _, issues = validate_duplicates(data)
        results["checks_performed"].append("duplicates")
        results["issues_found"].extend(issues)
        results["summary"]["duplicates"] = {
            "affected_rows": sum(_issue_affected_count(issue) for issue in issues)
        }
    if "duplicate_ohlc_rows" in checks:
        _, issues = validate_duplicate_ohlc_rows(data)
        results["checks_performed"].append("duplicate_ohlc_rows")
        results["issues_found"].extend(issues)
        results["summary"]["duplicate_ohlc_rows"] = {
            "affected_rows": sum(_issue_affected_count(issue) for issue in issues)
        }
    if "flatlines" in checks:
        _, issues = validate_flatlines(
            data, min_run_length=int(kwargs.get("flatline_min_run", 10))
        )
        results["checks_performed"].append("flatlines")
        results["issues_found"].extend(issues)
        results["summary"]["flatlines"] = {
            "affected_rows": sum(_issue_affected_count(issue) for issue in issues)
        }
    if "spread" in checks:
        stats, issues = validate_spread(
            data,
            max_allowed_spread=kwargs.get("max_allowed_spread"),
            z_score_threshold=float(kwargs.get("spread_z_score_threshold", 4.0)),
        )
        results["checks_performed"].append("spread")
        results["issues_found"].extend(issues)
        results["summary"]["spread"] = {
            "spread_stats": stats,
            "spread_issues_count": len(issues),
            "affected_rows": sum(_issue_affected_count(issue) for issue in issues),
        }
    symbol_profile, symbol_issues = _validate_symbol_consistency(
        raw_input, kwargs.get("symbol")
    )
    results["summary"]["symbol_verification"] = symbol_profile
    results["issues_found"].extend(symbol_issues)
    results["summary"]["timeframe"] = {
        "timeframe": kwargs.get("timeframe"),
        "expected_frequency": str(expected_frequency)
        if expected_frequency is not None
        else None,
    }
    minimum_rows = kwargs.get("minimum_rows")
    if minimum_rows is not None and len(data) < int(minimum_rows):
        results["checks_performed"].append("minimum_history")
        results["issues_found"].append(
            {
                "type": "minimum_history",
                "check": "minimum_rows",
                "count": max(int(minimum_rows) - len(data), 1),
                "required_rows": int(minimum_rows),
                "actual_rows": len(data),
            }
        )
    results["issues_found"] = validate_annotate_issues(results["issues_found"])
    remediation = validate_remediation_summary(results["issues_found"])
    results["summary"]["remediation"] = remediation
    results["summary"]["total_issues"] = len(results["issues_found"])
    results["summary"]["quality_penalty_breakdown"] = _quality_penalty_breakdown(
        results["issues_found"], max(len(data), 1)
    )
    results["summary"]["quality_score"] = _quality_score_from_issues(
        results["issues_found"], max(len(data), 1)
    )
    results["summary"]["is_valid"] = not remediation["needs_immediate_action"]
    results["summary"]["has_warnings"] = any(
        issue.get("severity") in {"medium", "low"} for issue in results["issues_found"]
    )
    results["decision"] = _build_quality_decision(results, profile, decision_settings)
    logger.info(
        f"OHLCV quality check completed. Quality Score: {results['summary']['quality_score']:.1f}%; decision={results['decision']['admission']} for profile={profile}."
    )
    if return_report:
        return DataQualityReport(
            timestamp=results["timestamp"],
            total_rows=len(data),
            checks_performed=results["checks_performed"],
            issues_found=results["issues_found"],
            summary=results["summary"],
            quality_score=results["summary"]["quality_score"],
            is_valid=results["summary"]["is_valid"],
            price_sanity_valid=results["summary"]
            .get("price_sanity", {})
            .get("all_valid", True),
            gaps_count=results["summary"]
            .get("gaps", {})
            .get("estimated_missing_periods", 0),
            anomalies_count=results["summary"]
            .get("spikes", {})
            .get("affected_rows", 0),
            missing_timestamps_count=results["summary"]
            .get("coverage", {})
            .get("missing_timestamps_count", 0),
            zero_volume_count=results["summary"]
            .get("zero_volume", {})
            .get("affected_rows", 0),
            duplicates_count=results["summary"]
            .get("duplicates", {})
            .get("affected_rows", 0),
            spread_stats=results["summary"].get("spread", {}).get("spread_stats"),
            has_warnings=results["summary"]["has_warnings"],
            coverage_ratio=results["summary"].get("coverage", {}).get("coverage_ratio"),
        )
    return results


def _json_safe_quality_value(value: Any) -> Any:
    """Return a JSON-safe representation for quality diagnostics."""
    if isinstance(value, datetime):
        timestamp = value
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        logger.debug("Implemented json safe quality value")
        return timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        logger.debug("Implemented json safe quality value")
        return {str(key): _json_safe_quality_value(item) for key, item in value.items()}
    if isinstance(value, list):
        logger.debug("Implemented json safe quality value")
        return [_json_safe_quality_value(item) for item in value]
    if isinstance(value, tuple):
        logger.debug("Implemented json safe quality value")
        return [_json_safe_quality_value(item) for item in value]
    if hasattr(value, "item"):
        try:
            logger.debug("Implemented json safe quality value")
            return value.item()
        except Exception:
            pass
    logger.debug("Implemented json safe quality value")
    return value


def validate_ohlcv_quality(
    data: pd.DataFrame,
    checks: list[str] | None = None,
    return_report: bool = False,
    *,
    profile: str = "research",
    z_score_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
    atr_window: int = 14,
    max_issues: int = 100,
    request_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Validate OHLCV market data quality using the official tool envelope.

    Args:
        data: OHLCV dataframe-compatible input.
        checks: Optional checks to run.
        return_report: Kept for compatibility; report fields are serialized into data.
        profile: Validation profile.
        z_score_threshold: Z-score threshold for spike checks.
        iqr_multiplier: IQR multiplier for spike checks.
        atr_window: ATR window for spike checks.
        max_issues: Maximum issues returned in the envelope.
        request_id: Optional request identifier.
        **kwargs: Additional engine options.

    Returns:
        Standard HaruQuant tool response with bounded quality diagnostics.
    """
    tool_name = "validate_ohlcv_quality"
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    started_at = datetime.now(UTC)
    try:
        result = _validate_ohlcv_quality_engine(
            data,
            checks=checks,
            return_report=return_report,
            profile=profile,
            z_score_threshold=z_score_threshold,
            iqr_multiplier=iqr_multiplier,
            atr_window=atr_window,
            **kwargs,
        )
        if isinstance(result, DataQualityReport):
            result_data: dict[str, Any] = {
                "timestamp": result.timestamp,
                "total_rows": result.total_rows,
                "checks_performed": result.checks_performed,
                "issues_found": result.issues_found,
                "summary": result.summary,
                "quality_score": result.quality_score,
                "is_valid": result.is_valid,
                "has_warnings": result.has_warnings,
            }
        else:
            result_data = dict(result)
        issues = list(result_data.get("issues_found", []))
        result_data["issues_found"] = issues[:max_issues]
        result_data["truncated"] = len(issues) > max_issues
        result_data["issue_count"] = len(issues)
        summary = result_data.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}
        is_valid = bool(summary.get("is_valid", False))
        execution_ms = round((datetime.now(UTC) - started_at).total_seconds() * 1000, 3)
        return standard_tool_response(
            spec,
            "success" if is_valid else "error",
            "OHLCV quality validation passed."
            if is_valid
            else "OHLCV quality validation failed.",
            data=_json_safe_quality_value(result_data),
            error=None
            if is_valid
            else {
                "code": "DATA_QUALITY_FAILED",
                "details": f"{len(issues)} quality issue(s) found.",
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as error:
        execution_ms = round((datetime.now(UTC) - started_at).total_seconds() * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return standard_tool_response(
            spec,
            "error",
            "OHLCV quality validation failed.",
            data=None,
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


class DataSource(Protocol):
    """
    Protocol for pluggable market data sources.

    This ensures that any data source implementation provides a standard
    `fetch_data` method for OHLCV retrieval.
    """

    def fetch_data(
        self, symbol: str, timeframe: str, start_pos: int, end_pos: int
    ) -> pd.DataFrame | None:
        """
        Fetch OHLCV data for the requested range.

        Args:
            symbol (str): Asset symbol.
            timeframe (str): Bar timeframe (e.g., 'M1', 'H1').
            start_pos (int): Starting position (bar offset).
            end_pos (int): Ending position (bar offset).

        Returns:
            Optional[pd.DataFrame]: Fetched OHLCV data or None if unavailable.
        """
        ...


@dataclass(frozen=True)
class OHLCVSchema:
    """
    Expected OHLCV column name mapping.

    Args:
        open (str): Column name for open price.
        high (str): Column name for high price.
        low (str): Column name for low price.
        close (str): Column name for close price.
        volume (str): Column name for volume.
        spread (str): Column name for spread.
    """

    open: str = "Open"
    high: str = "High"
    low: str = "Low"
    close: str = "Close"
    volume: str = "Volume"
    spread: str = "Spread"


DEFAULT_SCHEMA = OHLCVSchema()


def get_session_ranges(df: pd.DataFrame, session: str) -> pd.DataFrame:
    """
    Get bars belonging to a specific session.

    Logic:
    1. Ensures the 'session' column exists by tagging if necessary.
    2. Filters rows where the session matches the target.

    Args:
        df (pd.DataFrame): Input DataFrame.
        session (str): Session name (e.g., 'london', 'new_york').

    Returns:
        pd.DataFrame: Filtered session data.
    """
    if "session" not in df.columns:
        from app.services.research.session_config import tag_sessions

        df = tag_sessions(df)
    result = df[df["session"] == session].copy()
    logger.info(f"Filtered {len(result)} bars for session '{session}'.")
    return result


def compute_session_stats(
    df: pd.DataFrame,
    close_col: str = "Close",
    high_col: str = "High",
    low_col: str = "Low",
) -> pd.DataFrame:
    """
    Compute per-session statistics (mean return, volatility, range).

    Logic:
    1. Tags sessions if missing.
    2. Calculates log returns and high-low range.
    3. Groups by session and aggregates mean/std for returns and range.
    4. Returns a summary DataFrame indexed by session.

    Args:
        df (pd.DataFrame): Input DataFrame.
        close_col (str): Close price column.
        high_col (str): High price column.
        low_col (str): Low price column.

    Returns:
        pd.DataFrame: Per-session statistics.
    """
    if "session" not in df.columns:
        from app.services.research.session_config import tag_sessions

        df = tag_sessions(df)
    df = df.copy()
    df["returns"] = np.log(df[close_col] / df[close_col].shift(1))
    df["range"] = df[high_col] - df[low_col]
    stats = df.groupby("session").agg(
        {"returns": ["mean", "std", "count"], "range": ["mean", "std"]}
    )
    stats.columns = ["_".join(col).strip() for col in stats.columns.values]
    stats = stats.rename(
        columns={
            "returns_mean": "mean_return",
            "returns_std": "volatility",
            "returns_count": "n_bars",
            "range_mean": "avg_range",
            "range_std": "range_std",
        }
    )
    logger.info(f"Session stats computed for: {stats.index.tolist()}")
    return stats


def _synthesize_ohlcvs_columns(df: pd.DataFrame, schema: Any) -> pd.DataFrame:
    """Ensure canonical volume and spread columns exist for analysis."""
    out = df.copy()
    if schema.volume not in out.columns:
        out[schema.volume] = 0.0
    if schema.spread not in out.columns:
        prepared = prepare_ohlcv_data(out, schema=schema)
        out[schema.spread] = prepared[schema.spread].to_numpy()
        if schema.volume in prepared.columns:
            out[schema.volume] = prepared[schema.volume].to_numpy()
    logger.debug("Implemented synthesize ohlcvs columns")
    return out


def _ctx(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract context fields from keyword arguments."""
    logger.debug("Implemented ctx")
    return {
        "request_id": kwargs.get("request_id"),
        "agent_name": kwargs.get("agent_name"),
        "environment": kwargs.get("environment", "development"),
        "dry_run": kwargs.get("dry_run", True),
    }


def _business(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract business logic fields from keyword arguments."""
    logger.debug("Implemented business")
    return {
        key: value
        for key, value in kwargs.items()
        if key not in {"request_id", "agent_name", "environment", "dry_run"}
    }


__all__ = [
    "DataQualityReport",
    "DataSource",
    "OHLCVSchema",
    "compute_session_stats",
    "get_session_ranges",
    "prepare_ohlcv_data",
    "validate_annotate_issues",
    "validate_approval_packet",
    "validate_artifact_reference",
    "validate_blocked_actions",
    "validate_data_freshness",
    "validate_duplicate_ohlc_rows",
    "validate_duplicates",
    "validate_environment_mode",
    "validate_evidence_pack",
    "validate_find_column",
    "validate_find_columns",
    "validate_flatlines",
    "validate_gaps",
    "validate_get_time_series",
    "validate_handoff_payload",
    "validate_high_low",
    "validate_input_schema",
    "validate_issue_remediation_action",
    "validate_issue_severity",
    "validate_market_calendar_gaps",
    "validate_missing_timestamps",
    "validate_monotonic_timestamps",
    "validate_negative_prices",
    "validate_numeric_integrity",
    "validate_numeric_range",
    "validate_ohlcv_quality",
    "validate_output_schema",
    "validate_price_in_range",
    "validate_price_sanity",
    "validate_registry_entry",
    "validate_remediation_summary",
    "validate_required_fields",
    "validate_spikes",
    "validate_spread",
    "validate_timezone_awareness",
    "validate_zero_prices",
    "validate_zero_volume",
]
