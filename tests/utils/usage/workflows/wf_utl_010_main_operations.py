"""WF-UTL-010: exercise surviving legacy Utils operations through current APIs."""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_USAGE_ROOT = Path(__file__).resolve().parents[1]
for _path in (_REPOSITORY_ROOT, _USAGE_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from app.utils import (  # noqa: E402
    build_event_envelope,
    build_response_metadata,
    build_validation_outcome,
    canonical_digest,
    canonical_json,
    create_auth_context,
    create_validation_error,
    derive_stable_id,
    error_response,
    generate_id,
    get_app_settings_model_config,
    get_common_error_catalog,
    get_error_metadata,
    get_logger,
    map_exception,
    normalize_error_code,
    parse_event_envelope,
    redact_mapping_value,
    redact_text_value,
    route_error_event,
    success_response,
    utc_now,
    validate_reason_code,
)
from notification_runtime import run_real_notification_evidence  # noqa: E402

WORKFLOW_ID = "WF-UTL-010"


def _stage(number: int, title: str) -> None:
    """Print one stage heading.

    Args:
        number: One-based stage number.
        title: Bounded stage description.

    Returns:
        None.
    """
    print(f"\n{'=' * 88}\nStage {number}/9 — {title}\n{'=' * 88}")


def _logging_example() -> dict[str, object]:
    """Exercise levels, exception capture, and bound logging context."""
    logger = get_logger(__name__)
    logger.debug("Main operations debug evidence")
    logger.info("Main operations info evidence")
    logger.warning("Main operations warning evidence")
    logger.error("Main operations error evidence")
    logger.critical("Main operations critical evidence")
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        logger.exception("Main operations captured expected arithmetic failure")
    logger.bind(request_id="req-main-operations", user_id="USER-A").info(
        "Processing example operation with contextual metadata"
    )
    logger.bind(log_type="access", user_id="USER-A").info(
        "Example authenticated operation completed"
    )
    return {"levels": 5, "exception_captured": True, "bound_context": True}


def _error_example() -> dict[str, object]:
    """Exercise current error creation, normalization, mapping, and routing."""
    error = create_validation_error("VALIDATION_FAILED", "VALUE_INVALID")
    normalized = normalize_error_code(" invalid input ")
    metadata = get_error_metadata(normalized)
    mapped = map_exception(ValueError("password=must-not-escape"))
    delivered: list[dict[str, str]] = []
    routed = route_error_event(error, delivered.append)
    assert "must-not-escape" not in str(mapped)
    return {
        "normalized": normalized,
        "severity": metadata.severity,
        "mapped_code": mapped["code"],
        "routed_code": routed["code"],
        "sink_count": len(delivered),
    }


def _response_example() -> dict[str, object]:
    """Exercise standard responses, stable identity, and canonical serialization."""
    started = time.perf_counter_ns()
    metadata = build_response_metadata(
        name="utils.main_operations",
        domain="utils",
        risk_level="none",
        request_id=generate_id("req"),
        start_time=started,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        correlation_id=generate_id("cor"),
    )
    payload = {"symbol": "EURUSD", "result": 42}
    succeeded = success_response(
        payload, message="Calculation succeeded", metadata=metadata
    )
    failed = error_response(
        code="VALIDATION_FAILED",
        details={"field": "value"},
        message="Calculation failed",
        metadata=metadata,
        catalog=get_common_error_catalog(),
    )
    canonical = canonical_json(payload)
    return {
        "success": succeeded.error is None,
        "error_code": failed.error.code if failed.error else None,
        "canonical": canonical,
        "fingerprint": derive_stable_id("id", canonical_digest(payload)),
    }


def _redaction_example() -> dict[str, object]:
    """Exercise current text, mapping, and key-classification redaction."""
    text = redact_text_value("API_KEY=synthetic-secret").value
    mapping = redact_mapping_value(
        {"user_id": "USER-A", "password": "synthetic", "nested": {"token": "x"}}
    ).value
    return {"text": text, "mapping": mapping}


def _settings_example() -> dict[str, object]:
    """Report current shared settings-source policy without reading secret values."""
    config = get_app_settings_model_config()
    return {
        "environment_prefix": config.get("env_prefix"),
        "extra_policy": config.get("extra"),
        "case_sensitive": config.get("case_sensitive"),
    }


def _validation_example() -> dict[str, object]:
    """Exercise the current strict validation-outcome taxonomy."""
    reason = validate_reason_code("INPUT.INVALID")
    outcome = build_validation_outcome(
        verdict="FAIL",
        check_id="legacy-input",
        evaluated_at=utc_now(),
        reason_codes=(reason,),
        severity="ERROR",
    )
    return {"verdict": outcome["verdict"], "reason_codes": outcome["reason_codes"]}


def _event_example() -> dict[str, object]:
    """Exercise the immutable event envelope replacing the legacy event bus."""
    envelope = build_event_envelope(
        event_id="evt-main-operations",
        source_id="utils-usage",
        source_sequence=1,
        correlation_id="cor-main-operations",
        causation_id=None,
        deduplication_key="main-operations-1",
        emitted_at=utc_now(),
        payload={"action": "BUY", "symbol": "EURUSD", "token": "synthetic"},
    )
    parsed = parse_event_envelope(envelope)
    return {
        "schema_id": parsed["schema_id"],
        "source_sequence": parsed["source_sequence"],
        "payload": parsed["payload"],
    }


def _auth_example() -> dict[str, object]:
    """Exercise current immutable authentication-context evidence."""
    context = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="service-main-operations",
        principal_type="SERVICE_ACCOUNT",
        roles=("operator",),
        permissions=("utils:read",),
        scopes=("utils",),
        tenant_or_environment="dev",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=datetime.now(UTC),
    )
    return {
        "principal_id": context.principal_id,
        "principal_type": context.principal_type,
        "environment": context.tenant_or_environment,
    }


def main() -> None:
    """Run current equivalents of every surviving legacy Utils operation."""
    print(f"{WORKFLOW_ID} — Main Utils Operations")
    results: dict[str, object] = {}

    _stage(1, "Structured logging, exception capture, and bound context")
    results["logging"] = _logging_example()
    print(results["logging"])

    _stage(2, "Error normalization, mapping, metadata, and routing")
    results["errors"] = _error_example()
    print(results["errors"])

    _stage(3, "Standard responses, canonical JSON, and stable identity")
    results["responses"] = _response_example()
    print(results["responses"])

    _stage(4, "Sensitive text and mapping redaction")
    results["redaction"] = _redaction_example()
    print(results["redaction"])

    _stage(5, "Shared settings-source policy")
    results["settings"] = _settings_example()
    print(results["settings"])

    _stage(6, "Validation outcome and reason taxonomy")
    results["validation"] = _validation_example()
    print(results["validation"])

    _stage(7, "Immutable event envelope replacing the removed event bus")
    results["event"] = _event_example()
    print(results["event"])

    _stage(8, "Immutable authentication context without authorization policy")
    results["auth"] = _auth_example()
    print(results["auth"])

    _stage(9, "Real non-production notification delivery")
    results["notifications"] = dict(run_real_notification_evidence(WORKFLOW_ID))
    print(results["notifications"])

    print(
        "\nExcluded legacy ownership: paths, DataFrames, OHLCV quality, circuit breakers, metrics, password hashing, encryption, and authorization policy."
    )
    print("SUCCESS: WF-UTL-010 main operations completed")
    print(f"Data -> completed_stages={len(results)}, operations={tuple(results)}")


if __name__ == "__main__":
    main()
