"""Homogeneous full-domain usage program for app.utils.

Ties all Utils features (FEAT-UTIL-00 through FEAT-UTIL-08) into one sequential,
realistic end-to-end domain pipeline:
1. Settings Bootstrap (FEAT-UTIL-06)
2. Structured Logging Setup & Execution (FEAT-UTIL-07)
3. Trace Identity & Aware UTC Clocks (FEAT-UTIL-02, FEAT-UTIL-03)
4. AuthContext & AuditEvent Contracts (FEAT-UTIL-00)
5. Sensitive Data Redaction (FEAT-UTIL-05)
6. Canonical Serialization & Digesting (FEAT-UTIL-04)
7. Shared Error Mapping, Metadata & Event Routing (FEAT-UTIL-01)
8. Standard Operation Responses (FEAT-UTIL-08)
"""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.utils import (
    add_exact,
    age_seconds,
    attempt_transition,
    build_exact_unit,
    build_reservation,
    build_response_metadata,
    build_transition_table,
    build_validation_outcome,
    canonical_digest,
    canonical_json,
    configure_logging,
    create_audit_event,
    create_auth_context,
    derive_idempotency_key,
    derive_random_stream,
    derive_stable_id,
    error_response,
    evaluate_reservation,
    exception_response,
    flush_logging,
    format_utc_timestamp,
    generate_id,
    get_audit_event_type,
    get_auth_context_type,
    get_common_error_catalog,
    get_default_redaction_policy,
    get_error_metadata,
    get_execution_ms,
    get_logger,
    get_logger_handler_count,
    get_logger_name,
    get_standard_response_type,
    is_fresh,
    is_sensitive_key,
    load_broker_provider_settings,
    load_settings,
    log_info,
    map_exception,
    next_int,
    normalize_error_code,
    parse_utc_timestamp,
    redact_mapping_value,
    redact_text_value,
    require_error_definition,
    route_error_event,
    shutdown_logging,
    success_response,
    to_json_safe,
    utc_now,
    validate_error_catalog,
    validate_id,
)


def _run_stage_9_new_primitives() -> None:
    """Execute FEAT-UTIL-09 through FEAT-UTIL-13 in dependency order."""
    _print_stage(
        9,
        "Cockpit Foundation Primitives",
        "Exercise exact units, transitions, validation, idempotency, and seeded draws.",
    )
    amount = add_exact(
        build_exact_unit("1", kind="MONEY", currency="USD"),
        build_exact_unit("2", kind="MONEY", currency="USD"),
    )
    table = build_transition_table(
        {"OPEN": ["CLOSED"], "CLOSED": []}, terminal_states=["CLOSED"]
    )
    transition = attempt_transition(table, "OPEN", "CLOSED")
    instant = datetime(2026, 1, 1, tzinfo=UTC)
    validation = build_validation_outcome(
        verdict="PASS", check_id="pipeline", evaluated_at=instant
    )
    key = derive_idempotency_key(owner="utils:pipeline", intent={"operation": "demo"})
    reservation = build_reservation(key=key, reserved_at=instant, ttl_seconds=30)
    verdict = evaluate_reservation(
        key=key,
        owner="utils:pipeline",
        prior_reservation=reservation,
        observed_at=instant,
    )
    draw, _ = next_int(derive_random_stream(7, "pipeline"), lower=1, upper=10)
    print(
        f"Data -> amount={amount['amount']}, transition={transition['outcome']}, validation={validation['verdict']}, duplicate={verdict['verdict']}, draw={draw}"
    )


def _print_stage(stage_num: int, name: str, summary: str) -> None:
    print(f"\n[{'=' * 80}]")
    print(f"Stage {stage_num}: {name}")
    print(f"Description: {summary}")
    print(f"[{'=' * 80}]")


def _run_stage_1_settings() -> Any:
    _print_stage(
        1,
        "Settings Bootstrap (FEAT-UTIL-06)",
        "Load runtime configuration and broker provider settings in precedence order.",
    )
    runtime_settings = load_settings(
        explicit_values={"ENVIRONMENT": "dev", "LOG_LEVEL": "INFO"}
    )
    broker_settings: Any = load_broker_provider_settings()
    providers = {
        "binance": getattr(broker_settings, "binance_enabled", False),
        "mt5": getattr(broker_settings, "mt5_enabled", False),
    }
    print(
        f"Data -> environment='{runtime_settings.environment}', "
        f"profile='{runtime_settings.runtime_profile}', "
        f"broker_providers={providers}"
    )
    return runtime_settings


def _run_stage_2_logging(logging_settings: Any) -> Any:
    _print_stage(
        2,
        "Structured Logging Setup (FEAT-UTIL-07)",
        "Configure logger, query name/handlers, emit structured log, flush, and shutdown.",
    )
    logger = get_logger("haruquant.pipeline")
    logger_name = get_logger_name(logger)
    configure_logging(settings=logging_settings)
    handler_count = get_logger_handler_count(logger)

    bound_logger = logger.bind(pipeline_stage="bootstrap")
    log_info(
        bound_logger, "domain_pipeline_started", context={"status": "initializing"}
    )
    flush_logging()
    print(f"Data -> logger_name='{logger_name}', handlers_configured={handler_count}")
    return logger


def _run_stage_3_identity_and_clock() -> dict[str, Any]:
    _print_stage(
        3,
        "Trace Identity & UTC Clock (FEAT-UTIL-02 & FEAT-UTIL-03)",
        "Generate trace IDs, derive stable ID, read aware UTC time, format/parse, check freshness.",
    )
    start_mono = time.perf_counter_ns()
    req_id = generate_id("req")
    wf_id = generate_id("wf")
    cor_id = generate_id("cor")
    validated_req_id = validate_id(req_id, expected_prefix="req")
    stable_id = derive_stable_id("id", "pipeline_seed_material")
    now = utc_now()
    formatted_ts = format_utc_timestamp(now)
    parsed_ts = parse_utc_timestamp(formatted_ts)
    elapsed = age_seconds(parsed_ts, reference=now)
    fresh_verdict = is_fresh(parsed_ts, reference=now, max_age_seconds=Decimal(10))

    print(
        f"Data -> req_id='{validated_req_id}', stable_id='{stable_id[:16]}...', "
        f"utc='{formatted_ts}', age_s={elapsed}, is_fresh={fresh_verdict}"
    )
    return {
        "start_mono": start_mono,
        "req_id": req_id,
        "wf_id": wf_id,
        "cor_id": cor_id,
        "now": now,
    }


def _run_stage_4_contracts(trace_info: dict[str, Any]) -> Any:
    _print_stage(
        4,
        "AuthContext & AuditEvent Contracts (FEAT-UTIL-00)",
        "Construct immutable principal context and audit event envelopes.",
    )
    auth_ctx = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="service-pipeline",
        principal_type="SERVICE_ACCOUNT",
        roles=("operator",),
        permissions=("pipeline:execute",),
        scopes=("domain:utils",),
        tenant_or_environment="dev",
        request_id=trace_info["req_id"],
        workflow_id=trace_info["wf_id"],
        correlation_id=trace_info["cor_id"],
        issued_at=trace_info["now"],
    )
    audit_evt = create_audit_event(
        contract_version="v1",
        schema_id="utils.audit_event.v1",
        event_id=generate_id("evt"),
        timestamp=trace_info["now"],
        domain="utils",
        action="pipeline.execute",
        principal_id=auth_ctx.principal_id,
        request_id=trace_info["req_id"],
        correlation_id=trace_info["cor_id"],
        causation_id=None,
        payload={"status": "running"},
    )
    auth_type = get_auth_context_type()
    audit_type = get_audit_event_type()

    print(
        f"Data -> principal_id='{auth_ctx.principal_id}', "
        f"audit_action='{audit_evt.action}', "
        f"types=({auth_type.__name__}, {audit_type.__name__})"
    )
    return auth_ctx


def _run_stage_5_redaction() -> dict[str, Any]:
    _print_stage(
        5,
        "Sensitive Data Redaction (FEAT-UTIL-05)",
        "Check sensitive keys and perform denylist-first redaction on text and mappings.",
    )
    policy = get_default_redaction_policy()
    has_secret_key = is_sensitive_key("api_secret_key")

    raw_text = "authorization: Bearer synthetic_token_value"  # pragma: allowlist secret
    redacted_text = redact_text_value(raw_text, policy=policy).value

    raw_mapping = {
        "user": "operator_1",
        "api_key": "synthetic_key_value",  # pragma: allowlist secret
        "nested": {
            "client_secret": "synthetic_secret_value",  # pragma: allowlist secret
        },
    }
    redacted_mapping = redact_mapping_value(raw_mapping, policy=policy).value

    print(
        f"Data -> is_sensitive={has_secret_key}, "
        f"redacted_text='{redacted_text}', "
        f"redacted_mapping={redacted_mapping}"
    )
    return redacted_mapping


def _run_stage_6_serialization(
    now: Any, req_id: str, redacted_mapping: dict[str, Any]
) -> str:
    _print_stage(
        6,
        "Canonical Serialization & Digesting (FEAT-UTIL-04)",
        "Convert types to JSON-safe, serialize deterministically, and compute SHA-256 digest.",
    )
    payload_data: dict[str, Any] = {
        "timestamp": now,
        "redacted_mapping": redacted_mapping,
        "request_id": req_id,
    }
    json_safe_data = to_json_safe(payload_data)
    canonical_str = canonical_json(json_safe_data)
    digest_hash = canonical_digest(json_safe_data)

    print(
        f"Data -> json_safe_keys={list(json_safe_data.keys())}, "
        f"canonical_len={len(canonical_str)}, "
        f"digest='{digest_hash[:16]}...'"
    )
    return digest_hash


def _run_stage_7_error_routing() -> Any:
    _print_stage(
        7,
        "Shared Error Mapping & Event Routing (FEAT-UTIL-01)",
        "Map exception, validate error catalog, resolve metadata, require definition, route error.",
    )
    common_catalog = get_common_error_catalog()
    validate_error_catalog(common_catalog)

    mapped_err = map_exception(ValueError("invalid parameter provided"))
    norm_code = normalize_error_code(mapped_err["code"])
    err_def = require_error_definition(norm_code, catalog=common_catalog)
    err_metadata = get_error_metadata(norm_code)

    routed_events: list[dict[str, str]] = []

    def _mock_sink(event: dict[str, str]) -> None:
        routed_events.append(event)

    route_error_event(ValueError("demonstration pipeline error"), sink=_mock_sink)

    print(
        f"Data -> mapped_code='{norm_code}', "
        f"def_code='{err_def.code}', "
        f"severity='{err_metadata.severity}', "
        f"routed_count={len(routed_events)}"
    )
    return common_catalog


def _run_stage_8_responses(
    trace_info: dict[str, Any], digest_hash: str, common_catalog: Any
) -> None:
    _print_stage(
        8,
        "Standard Operation Responses (FEAT-UTIL-08)",
        "Build response metadata, elapsed timing, and construct StandardResponse envelopes.",
    )
    metadata = build_response_metadata(
        name="utils.pipeline_example",
        domain="utils",
        risk_level="none",
        request_id=trace_info["req_id"],
        correlation_id=trace_info["cor_id"],
        start_time=trace_info["start_mono"],
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
    )
    success_env = success_response(
        data={"pipeline_status": "completed", "digest": digest_hash},
        message="Full Utils domain pipeline completed successfully",
        metadata=metadata,
    )
    err_env = error_response(
        code="VALIDATION_FAILED",
        details={"field": "sample_field", "reason": "Sample domain validation failure"},
        message="Pipeline validation error demo",
        metadata=metadata,
        catalog=common_catalog,
    )
    exc_env = exception_response(
        exception=RuntimeError("unexpected runtime error"),
        message="Pipeline exception demo",
        metadata=metadata,
        catalog=common_catalog,
    )
    exec_ms = get_execution_ms(trace_info["start_mono"])
    resp_type = get_standard_response_type()

    print(
        f"Data -> success_status='{success_env.status}', "
        f"err_code='{err_env.error.code}', "
        f"exc_code='{exc_env.error.code}', "
        f"exec_ms={exec_ms}, "
        f"resp_type={resp_type.__name__}"
    )


def main() -> None:
    """Execute complete end-to-end Utils domain pipeline."""
    print("=" * 88)
    print("UTILS DOMAIN: FULL HOMOGENEOUS END-TO-END PIPELINE EXAMPLE")
    print(
        "Ties FEAT-UTIL-00 through FEAT-UTIL-08 sequentially in realistic runtime order."
    )
    print("=" * 88)

    runtime_settings = _run_stage_1_settings()
    _run_stage_2_logging(runtime_settings.logging)
    trace_info = _run_stage_3_identity_and_clock()
    _run_stage_4_contracts(trace_info)
    redacted_mapping = _run_stage_5_redaction()
    digest_hash = _run_stage_6_serialization(
        trace_info["now"], trace_info["req_id"], redacted_mapping
    )
    common_catalog = _run_stage_7_error_routing()
    _run_stage_8_responses(trace_info, digest_hash, common_catalog)
    _run_stage_9_new_primitives()

    shutdown_logging()

    print("\n" + "=" * 88)
    print("Data -> full_domain_pipeline_status='completed'")
    print("SUCCESS: All 14 Utils features executed in realistic pipeline order!")
    print("=" * 88)


if __name__ == "__main__":
    main()
