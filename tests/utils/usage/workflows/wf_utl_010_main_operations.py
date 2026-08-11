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
STAGES = (
    "Structured logging, exception capture, and bound context",
    "Error normalization, mapping, metadata, and routing",
    "Standard responses, canonical JSON, and stable identity",
    "Sensitive text and mapping redaction",
    "Shared settings-source policy",
    "Validation outcome and reason taxonomy",
    "Immutable event envelope replacing the removed event bus",
    "Immutable authentication context without authorization policy",
    "Real non-production notification delivery",
)


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
    """Exercise levels, exception capture, and bound logging context in legacy style."""
    logger = get_logger(__name__)

    print("\n 1.1 Standard structured logging levels")
    logger.debug("This is a debug message containing developer details.")
    logger.info("This is an info message for standard application events.")
    logger.warning("This is a warning indicating a potential issue.")
    logger.error("This is an error indicating an execution failure.")
    logger.critical("This is a critical failure message.")

    print("\n 1.2 Logging exceptions with tracebacks")
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        logger.exception("Successfully captured an exception with traceback:")

    print("\n 1.3 Dynamic context logging using bind (Dynamic Contextual Metadata)")
    bound_logger = logger.bind(request_id="REQ-1002", user_id="USER-A")
    bound_logger.info("Processing order request with contextual metadata.")

    print("\n 1.4 Routing to Specialized Log Files")
    access_logger = logger.bind(log_type="access", user_id="USER-A")
    access_logger.info("User logged in successfully from 192.168.1.50")

    return {"levels": 5, "exception_captured": True, "bound_context": True}


def _error_example() -> dict[str, object]:
    """Exercise current error creation, normalization, metadata lookup, and routing."""
    print("\n 2.1 Raising typed error codes")
    try:
        raise create_validation_error("INVALID_INPUT", "VALUE_INVALID")  # noqa: TRY301
    except Exception as exc:  # noqa: BLE001
        print(f"Caught typed validation error: {exc}")

    print("\n 2.2 Normalizing and looking up error metadata")
    normalized = normalize_error_code(" invalid input ")
    metadata = get_error_metadata(normalized)
    print(f"Normalized ' invalid input ' -> {normalized}")
    print(f"Severity: {metadata.severity}")

    print("\n 2.3 Validating error codes strictly")
    reason = validate_reason_code("INPUT.INVALID")
    print(f"Validated reason code: {reason}")

    print("\n 2.4 Exception payload mapping helpers")
    raw_exc = ValueError("Invalid database format with password=must-not-escape.")
    mapped = map_exception(raw_exc)
    print(f"Mapped ValueError -> code: {mapped['code']}")
    print(f"Full payload: {mapped}")

    print("\n 2.5 Routing error events")
    delivered: list[dict[str, str]] = []
    error = create_validation_error("VALIDATION_FAILED", "VALUE_INVALID")
    routed = route_error_event(error, delivered.append)
    print(f"Route Status: delivered to {len(delivered)} sinks")
    print(f"Route Code: {routed['code']}")

    return {
        "normalized": normalized,
        "severity": metadata.severity,
        "mapped_code": mapped["code"],
        "routed_code": routed["code"],
        "sink_count": len(delivered),
    }


def _response_example() -> dict[str, object]:
    """Exercise standard response envelopes, canonical JSON, and stable identity."""
    started = time.perf_counter_ns()

    print("\n 3.1 Building standard metadata")
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
    print(f"Metadata domain: {metadata.domain}")

    print("\n 3.2 Generating a success response envelope")
    payload = {"symbol": "EURUSD", "period": 14, "mode": "strict"}
    succeeded = success_response(
        payload, message="Calculation succeeded.", metadata=metadata
    )
    print(f"Success Envelope: {succeeded.status}")

    print("\n 3.3 Generating an error response envelope")
    failed = error_response(
        code="VALIDATION_FAILED",
        details={"field": "value"},
        message="Calculation failed.",
        metadata=metadata,
        catalog=get_common_error_catalog(),
    )
    print(
        f"Error Envelope: {failed.status} (code: {failed.error.code if failed.error else None})"
    )

    print("\n 3.4 Response mapping from a raw exception")
    mapped_error = map_exception(ValueError("Division by zero in formula."))
    print(f"Exception Mapped Payload Code: {mapped_error['code']}")

    print("\n 3.5 Stable identifiers and canonical JSON")
    canonical = canonical_json(payload)
    fingerprint = derive_stable_id("id", canonical_digest(payload))
    print(f"Canonical JSON: {canonical}")
    print(f"Fingerprint ID: {fingerprint}")

    return {
        "success": succeeded.error is None,
        "error_code": failed.error.code if failed.error else None,
        "canonical": canonical,
        "fingerprint": fingerprint,
    }


def _redaction_example() -> dict[str, object]:
    """Exercise current text and mapping redaction."""
    print("\n 4.1 Redacting sensitive text and mappings")
    secret_text = "Standard request API_KEY=secret_key_12345 in header."
    redacted_text_out = redact_text_value(secret_text).value
    print(f"Redacted Text: {redacted_text_out}")

    payload = {
        "user_id": "USER-A",
        "password": "my_super_secret_password",
        "api_key": "12345-abcde",
        "nested": {"secret": "inner_secret"},
    }
    redacted_map = redact_mapping_value(payload).value
    print(f"Redacted Mapping: {redacted_map}")

    return {"text": redacted_text_out, "mapping": redacted_map}


def _settings_example() -> dict[str, object]:
    """Report current shared settings-source policy."""
    print("\n 5.1 Shared settings-source policy")
    config = get_app_settings_model_config()
    print(f"Environment Prefix: {config.get('env_prefix')}")
    print(f"Extra Policy: {config.get('extra')}")
    print(f"Case Sensitive: {config.get('case_sensitive')}")

    return {
        "environment_prefix": config.get("env_prefix"),
        "extra_policy": config.get("extra"),
        "case_sensitive": config.get("case_sensitive"),
    }


def _validation_example() -> dict[str, object]:
    """Exercise current strict validation-outcome taxonomy."""
    print("\n 6.1 Validation outcome and reason taxonomy")
    reason = validate_reason_code("INPUT.INVALID")
    outcome = build_validation_outcome(
        verdict="FAIL",
        check_id="legacy-input",
        evaluated_at=utc_now(),
        reason_codes=(reason,),
        severity="ERROR",
    )
    print(f"Validation Verdict: {outcome['verdict']}")
    print(f"Reason Codes: {outcome['reason_codes']}")

    return {"verdict": outcome["verdict"], "reason_codes": outcome["reason_codes"]}


def _event_example() -> dict[str, object]:
    """Exercise the immutable event envelope replacing the legacy event bus."""
    print("\n 7.1 Immutable event envelope replacing legacy event bus")
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
    print(f"Event Schema ID: {parsed['schema_id']}")
    print(f"Event Payload: {parsed['payload']}")

    return {
        "schema_id": parsed["schema_id"],
        "source_sequence": parsed["source_sequence"],
        "payload": parsed["payload"],
    }


def _auth_example() -> dict[str, object]:
    """Exercise current immutable authentication-context evidence."""
    print("\n 8.1 Immutable authentication context evidence")
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
    print(f"Auth Principal ID: {context.principal_id}")
    print(f"Auth Environment: {context.tenant_or_environment}")

    return {
        "principal_id": context.principal_id,
        "principal_type": context.principal_type,
        "environment": context.tenant_or_environment,
    }


def _notifications_example() -> dict[str, object]:
    """Exercise real non-production notification delivery."""
    print("\n 9.1 Real non-production notification delivery")
    evidence = dict(run_real_notification_evidence(WORKFLOW_ID))
    print(f"Notification Status: {evidence.get('status')}")
    return evidence


def main() -> None:
    """Run current equivalents of surviving legacy Utils operations in sectioned legacy style."""
    print(f"{WORKFLOW_ID} — Main Utils Operations")
    print("INPUT BOUNDARY — caller operations and explicit settings context")
    results: dict[str, object] = {}

    # Stage 1 — Structured logging, exception capture, and bound context
    _stage(1, "Structured logging, exception capture, and bound context")
    results["logging"] = _logging_example()
    print(results["logging"])

    # Stage 2 — Error normalization, mapping, metadata, and routing
    _stage(2, "Error normalization, mapping, metadata, and routing")
    results["errors"] = _error_example()
    print(results["errors"])

    # Stage 3 — Standard responses, canonical JSON, and stable identity
    _stage(3, "Standard responses, canonical JSON, and stable identity")
    results["responses"] = _response_example()
    print(results["responses"])

    # Stage 4 — Sensitive text and mapping redaction
    _stage(4, "Sensitive text and mapping redaction")
    results["redaction"] = _redaction_example()
    print(results["redaction"])

    # Stage 5 — Shared settings-source policy
    _stage(5, "Shared settings-source policy")
    results["settings"] = _settings_example()
    print(results["settings"])

    # Stage 6 — Validation outcome and reason taxonomy
    _stage(6, "Validation outcome and reason taxonomy")
    results["validation"] = _validation_example()
    print(results["validation"])

    # Stage 7 — Immutable event envelope replacing the removed event bus
    _stage(7, "Immutable event envelope replacing the removed event bus")
    results["event"] = _event_example()
    print(results["event"])

    # Stage 8 — Immutable authentication context without authorization policy
    _stage(8, "Immutable authentication context without authorization policy")
    results["auth"] = _auth_example()
    print(results["auth"])

    # Stage 9 — Real non-production notification delivery
    _stage(9, "Real non-production notification delivery")
    results["notifications"] = _notifications_example()
    print(results["notifications"])

    print(
        "\nExcluded legacy ownership: paths, DataFrames, OHLCV quality, circuit breakers, metrics, password hashing, encryption, and authorization policy."
    )
    print("SUCCESS: WF-UTL-010 main operations completed")
    print(f"Data -> completed_stages={len(results)}, operations={tuple(results)}")
    print("OUTPUT BOUNDARY — main operations completion state")


if __name__ == "__main__":
    main()
