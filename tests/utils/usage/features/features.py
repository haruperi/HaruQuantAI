"""Canonical 18-stage full-domain pipeline for all Utils features."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Mapping
from decimal import Decimal
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
_USAGE_ROOT = Path(__file__).resolve().parents[1]
for _path in (_REPOSITORY_ROOT, _USAGE_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from app.utils import (  # noqa: E402
    attempt_transition,
    build_event_envelope,
    build_exact_unit,
    build_reservation,
    build_response_metadata,
    build_transition_record,
    build_transition_table,
    build_validation_outcome,
    canonical_digest,
    canonical_json,
    combine_validation_outcomes,
    configure_logging,
    create_audit_event,
    create_auth_context,
    derive_idempotency_key,
    derive_random_stream,
    error_response,
    evaluate_reservation,
    exception_response,
    flush_logging,
    format_utc_timestamp,
    generate_id,
    get_common_error_catalog,
    get_logger,
    is_fresh,
    load_settings,
    map_exception,
    next_int,
    parse_event_envelope,
    parse_utc_timestamp,
    redact_mapping_value,
    route_error_event,
    shutdown_logging,
    success_response,
    to_json_safe,
    utc_now,
    validate_id,
)
from notification_runtime import run_real_notification_evidence  # noqa: E402

FEATURE_IDS = tuple(f"FEAT-UTIL-{number:02d}" for number in range(15))
STAGES = (
    "Load and validate runtime settings",
    "Configure redacting non-blocking logging",
    "Generate and validate operation identifiers",
    "Establish aware UTC time, sequencing, and freshness",
    "Construct immutable authentication context",
    "Convert inputs into JSON-safe primitives",
    "Redact sensitive inputs",
    "Construct exact unit-bearing values",
    "Build and combine validation outcomes",
    "Derive and reserve the idempotency key",
    "Derive a deterministic random stream",
    "Execute an injected domain-owned operation",
    "Validate and record the resulting state transition",
    "Redact, serialize, and digest the outcome",
    "Construct audit and event envelopes",
    "Construct success and normalized failure responses",
    "Render and dispatch real non-production notifications",
    "Emit completion telemetry, flush logging, and shut down",
)


def _stage(number: int) -> None:
    """Print one canonical pipeline stage heading.

    Args:
        number: One-based stage number.
    """
    print(f"\n{'=' * 88}\nStage {number}/18 — {STAGES[number - 1]}\n{'=' * 88}")


def _execute_domain_operation(
    operation: Callable[[Mapping[str, object]], Mapping[str, object]],
    inputs: Mapping[str, object],
) -> Mapping[str, object]:
    """Invoke an explicitly injected domain-owned operation boundary.

    Args:
        operation: Caller-owned deterministic operation.
        inputs: Validated, redacted operation inputs.

    Returns:
        Detached operation result.
    """
    return dict(operation(inputs))


def _demo_domain_operation(inputs: Mapping[str, object]) -> Mapping[str, object]:
    """Return a bounded deterministic result representing another domain.

    Args:
        inputs: Validated example inputs.

    Returns:
        Actual deterministic operation result.
    """
    return {
        "operation": "example.calculate",
        "symbol": inputs["symbol"],
        "result": int(str(inputs["quantity"])) * 2,
    }


def main() -> None:  # noqa: PLR0915 - stages intentionally mirror the specification.
    """Execute the complete Utils lifecycle around one injected operation."""
    print("UTILS DOMAIN — COMPLETE 18-STAGE PIPELINE")
    print(f"Registered features -> {FEATURE_IDS}")
    pipeline: dict[str, object] = {}
    started_ns = time.perf_counter_ns()

    _stage(1)
    settings = load_settings(
        explicit_values={"ENVIRONMENT": "dev", "LOG_LEVEL": "INFO"}
    )
    pipeline["settings"] = {
        "environment": settings.environment,
        "runtime_profile": settings.runtime_profile,
    }
    print(pipeline["settings"])

    _stage(2)
    configure_logging(settings=settings.logging)
    logger = get_logger("haruquant.utils.full_pipeline").bind(
        pipeline="utils-full-domain"
    )
    logger.info("Utils full-domain pipeline started")
    pipeline["logging"] = {"configured": True}
    print(pipeline["logging"])

    _stage(3)
    request_id = validate_id(generate_id("req"), expected_prefix="req")
    workflow_id = validate_id(generate_id("wf"), expected_prefix="wf")
    correlation_id = validate_id(generate_id("cor"), expected_prefix="cor")
    pipeline["identity"] = {
        "request_id": request_id,
        "workflow_id": workflow_id,
        "correlation_id": correlation_id,
    }
    print(pipeline["identity"])

    _stage(4)
    observed_at = utc_now()
    rendered_at = format_utc_timestamp(observed_at)
    parsed_at = parse_utc_timestamp(rendered_at)
    pipeline["time"] = {
        "timestamp": rendered_at,
        "sequence": 1,
        "fresh": is_fresh(
            parsed_at,
            reference=observed_at,
            max_age_seconds=Decimal(10),
        ),
    }
    print(pipeline["time"])

    _stage(5)
    auth_context = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="service-full-pipeline",
        principal_type="SERVICE_ACCOUNT",
        roles=("operator",),
        permissions=("example:execute",),
        scopes=("utils",),
        tenant_or_environment="dev",
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        issued_at=observed_at,
    )
    pipeline["auth"] = {
        "principal_id": auth_context.principal_id,
        "environment": auth_context.tenant_or_environment,
    }
    print(pipeline["auth"])

    raw_input = {
        "symbol": "EURUSD",
        "quantity": 2,
        "api_token": "synthetic-sensitive-value",
    }
    _stage(6)
    json_safe_input = to_json_safe(raw_input)
    pipeline["json_safe_input"] = json_safe_input
    print({"keys": tuple(json_safe_input)})

    _stage(7)
    redacted_input = redact_mapping_value(json_safe_input).value
    assert isinstance(redacted_input, dict)
    pipeline["redacted_input"] = redacted_input
    print(redacted_input)

    _stage(8)
    exact_quantity = build_exact_unit("2", kind="QUANTITY")
    pipeline["exact_units"] = exact_quantity
    print(exact_quantity)

    _stage(9)
    validation = build_validation_outcome(
        verdict="PASS",
        check_id="full-pipeline-input",
        evaluated_at=observed_at,
        reason_codes=(),
        severity="INFO",
    )
    combined_validation = combine_validation_outcomes((validation,))
    pipeline["validation"] = combined_validation
    print(combined_validation)

    _stage(10)
    idempotency_owner = "utils:full_pipeline"
    idempotency_intent = {
        "symbol": redacted_input["symbol"],
        "quantity": exact_quantity["amount"],
    }
    idempotency_key = derive_idempotency_key(
        owner=idempotency_owner,
        intent=idempotency_intent,
    )
    reservation = build_reservation(
        key=idempotency_key, reserved_at=observed_at, ttl_seconds=60
    )
    reservation_verdict = evaluate_reservation(
        key=idempotency_key,
        owner=idempotency_owner,
        prior_reservation=None,
        observed_at=observed_at,
    )
    pipeline["idempotency"] = {
        "reservation": reservation,
        "verdict": reservation_verdict,
    }
    print(reservation_verdict)

    _stage(11)
    random_value, random_stream = next_int(
        derive_random_stream(20260809, "utils-full-pipeline"), lower=1, upper=10
    )
    pipeline["random"] = {"draw": random_value, "stream": random_stream}
    print({"draw": random_value})

    _stage(12)
    operation_result = _execute_domain_operation(
        _demo_domain_operation,
        {"symbol": redacted_input["symbol"], "quantity": exact_quantity["amount"]},
    )
    pipeline["operation"] = operation_result
    print(operation_result)

    _stage(13)
    transition_table = build_transition_table(
        {"PENDING": ("COMPLETED", "FAILED"), "COMPLETED": (), "FAILED": ()},
        terminal_states=("COMPLETED", "FAILED"),
    )
    transition = attempt_transition(transition_table, "PENDING", "COMPLETED")
    transition_record = build_transition_record(
        entity_id="example-operation-001",
        source_state=str(transition["source_state"]),
        target_state=str(transition["target_state"]),
        outcome=str(transition["outcome"]),
        reason_code=str(transition["reason_code"]),
        actor_ref=auth_context.principal_id,
        occurred_at=observed_at,
        sequence=1,
    )
    pipeline["transition"] = transition_record
    print(transition_record)

    _stage(14)
    safe_outcome = redact_mapping_value(dict(operation_result)).value
    canonical_outcome = canonical_json(safe_outcome)
    outcome_digest = canonical_digest(safe_outcome)
    pipeline["canonical_outcome"] = {
        "json": canonical_outcome,
        "digest": outcome_digest,
    }
    print(pipeline["canonical_outcome"])

    _stage(15)
    audit_event = create_audit_event(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=observed_at,
        domain="example",
        action="operation.completed",
        principal_id=auth_context.principal_id,
        request_id=request_id,
        correlation_id=correlation_id,
        causation_id=None,
        payload={"digest": outcome_digest},
    )
    event_envelope = build_event_envelope(
        event_id=audit_event.event_id,
        source_id="example-domain",
        source_sequence=1,
        correlation_id=correlation_id,
        causation_id=None,
        deduplication_key=idempotency_key["digest"],
        emitted_at=observed_at,
        payload={"audit_action": audit_event.action, "result": operation_result},
    )
    parsed_envelope = parse_event_envelope(event_envelope)
    pipeline["contracts"] = {
        "audit_action": audit_event.action,
        "event_schema": parsed_envelope["schema_id"],
    }
    print(pipeline["contracts"])

    _stage(16)
    response_metadata = build_response_metadata(
        name="utils.full_domain_pipeline",
        domain="utils",
        risk_level="none",
        request_id=request_id,
        start_time=started_ns,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        correlation_id=correlation_id,
    )
    success = success_response(
        operation_result,
        message="Injected operation completed",
        metadata=response_metadata,
    )
    catalog = get_common_error_catalog()
    mapped_failure = map_exception(ValueError("synthetic invalid input"))
    routed_events: list[dict[str, str]] = []
    route_error_event(ValueError("synthetic invalid input"), routed_events.append)
    failure = error_response(
        code="VALIDATION_FAILED",
        details={"reason": "synthetic failure branch"},
        message="Injected operation rejected",
        metadata=response_metadata,
        catalog=catalog,
    )
    unexpected = exception_response(
        RuntimeError("synthetic unexpected branch"),
        message="Injected operation failed",
        metadata=response_metadata,
        catalog=catalog,
    )
    pipeline["responses"] = {
        "success": success.status,
        "mapped_failure": mapped_failure["code"],
        "failure": failure.error.code if failure.error else None,
        "unexpected": unexpected.error.code if unexpected.error else None,
        "routed_events": len(routed_events),
    }
    print(pipeline["responses"])

    _stage(17)
    notification = run_real_notification_evidence("UTILS-FULL-PIPELINE")
    pipeline["notification"] = dict(notification)
    print(pipeline["notification"])

    _stage(18)
    logger.info("Utils full-domain pipeline completed")
    flush_logging()
    shutdown_logging()
    pipeline["finalization"] = {"logs_flushed": True, "logging_stopped": True}
    print(pipeline["finalization"])

    print("SUCCESS: complete 18-stage Utils domain pipeline completed")
    print(
        "Data -> "
        f"completed_stages={len(STAGES)}, features={len(FEATURE_IDS)}, "
        f"operation_result={operation_result}, notification_status={notification['status']}"
    )


if __name__ == "__main__":
    main()
