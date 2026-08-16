# Legacy executable usage program.
"""Usage example showing logger logging in HaruQuant."""

import sys
from decimal import Decimal
from pathlib import Path

# Add project root to sys.path to allow direct execution
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import app  # noqa: F401


def example_01_logger_example() -> None:
    """Demonstrate how to log messages at various levels using logger."""
    print("\n" + "=" * 100)
    print("--- 1. Logging Example ---")
    print("=" * 100)

    from app.utils import get_logger

    logger = get_logger("01_utils")

    print("\n\n 1.1 Standard structured logging levels")
    logger.debug("This is a debug message containing developer details.")
    logger.info("This is an info message for standard application events.")
    logger.warning("This is a warning indicating a potential issue.")
    logger.error("This is an error indicating an execution failure.")
    logger.critical("This is a critical failure message.")

    print("\n\n 1.2 Logging exceptions with tracebacks")
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        logger.exception("Successfully captured an exception with traceback:")

    print("\n\n 1.3 Context logging with child loggers")
    child_logger = get_logger("01_utils.order_processor")
    child_logger.info("Processing order request with contextual metadata.")

    assert True


def example_02_error_handling_example() -> None:
    """Demonstrate HaruQuant deterministic error utility patterns."""
    print("\n" + "=" * 100)
    print("--- 2. Error Handling Example ---")
    print("=" * 100)

    from app.utils import (
        create_validation_error,
        get_error_metadata,
        map_exception,
        normalize_error_code,
        route_error_event,
    )

    print("\n\n 2.1 Raising typed error codes")
    err = create_validation_error("INVALID_INPUT", "INPUT_SIZE_EXCEEDED")
    print(f"Created validation error: {err}")

    print("\n\n 2.2 Normalizing and looking up error metadata")
    normalized = normalize_error_code("invalid_input")
    meta = get_error_metadata(normalized)
    print(f"Normalized 'invalid_input' -> {normalized}")
    print(f"Error Metadata: {meta}")

    print("\n\n 2.3 Exception payload mapping helpers")
    raw_exc = ValueError("Invalid database format.")
    mapped = map_exception(raw_exc)
    print(f"Mapped ValueError -> payload: {mapped}")

    print("\n\n 2.4 Routing error events")
    err_event = create_validation_error("DUPLICATE_TIMESTAMP", "TIMESTAMP_EXISTS")
    route_result = route_error_event(
        err_event, sink=lambda p: print(f"Sink received: {p}")
    )
    print(f"Route Event Status: {route_result}")

    assert True


def example_03_standard_tool_envelope_example() -> None:
    """Demonstrate Standard tool response envelopes and utility contracts."""
    print("\n" + "=" * 100)
    print("--- 3. Standard Tool Envelope Example ---")
    print("=" * 100)

    import time

    from app.utils import (
        build_response_metadata,
        canonical_json,
        derive_stable_id,
        error_response,
        exception_response,
        generate_id,
        get_common_error_catalog,
        success_response,
    )

    print("\n\n 3.1 Building standard metadata")
    metadata = build_response_metadata(
        name="example_calculator",
        domain="math",
        risk_level="low",
        request_id=generate_id("req"),
        start_time=time.perf_counter_ns(),
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
    )
    print(f"Metadata name: {metadata.name}")

    print("\n\n 3.2 Generating a success response envelope")
    success = success_response(
        {"result": 42.0},
        message="Calculation succeeded.",
        metadata=metadata,
    )
    print(f"Success Envelope: {success.status}")

    print("\n\n 3.3 Generating an error response envelope")
    error = error_response(
        code="VALIDATION_FAILED",
        details={"reason": "Value must be positive."},
        message="Calculation failed.",
        metadata=metadata,
        catalog=get_common_error_catalog(),
    )
    err_payload = error.error
    assert err_payload is not None
    print(f"Error Envelope: {error.status} (code: {err_payload.code})")

    print("\n\n 3.4 Response mapping from a raw exception")
    err_exc = ValueError("Division by zero in formula.")
    mapped_error = exception_response(
        err_exc,
        message="Formula evaluation failed.",
        metadata=metadata,
        catalog=get_common_error_catalog(),
    )
    print(f"Exception Mapped Envelope Status: {mapped_error.status}")

    print("\n\n 3.5 Stable identifiers and canonical JSON")
    payload = {"symbol": "EURUSD", "period": 14, "mode": "strict"}
    canonical = canonical_json(payload)
    fingerprint = derive_stable_id("id", canonical)
    print(f"Canonical JSON: {canonical}")
    print(f"Fingerprint ID: {fingerprint}")

    assert True


def example_04_safe_path_normalization_example() -> None:
    """Demonstrate safe path normalization and explicit directory creation."""
    print("\n" + "=" * 100)
    print("--- 4. Safe Path Normalization Example ---")
    print("=" * 100)

    import shutil

    print("\n\n 4.1 Normalizing paths")
    project_root = Path.cwd().resolve()
    temp_dir = project_root / "temp_usage_examples"
    temp_dir.mkdir(exist_ok=True)

    normalized = (temp_dir / "data" / "raw" / "feed.csv").resolve()
    print(f"Normalized: {normalized}")

    print("\n\n 4.2 Safe joining with traversal protection")
    joined = (temp_dir / "exports" / "reports" / "daily.pdf").resolve()
    print(f"Safe Joined: {joined}")

    print("\n\n 4.3 Validating external path bounds")
    is_safe = joined.is_relative_to(temp_dir)
    print(f"Path within root? {is_safe}")

    print("\n\n 4.4 Ensuring directory and parent creation")
    target_dir = temp_dir / "output_dir"
    target_file = target_dir / "nested_dir" / "results.json"

    target_dir.mkdir(parents=True, exist_ok=True)
    target_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"Directory exists: {target_dir.is_dir()}")
    print(f"Parent directory exists: {target_file.parent.is_dir()}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    assert True


def example_05_security_and_redaction() -> None:
    """Demonstrate security helpers for redaction and key classification."""
    print("\n" + "=" * 100)
    print("--- 5. Security and Redaction Example ---")
    print("=" * 100)

    from app.utils import (
        is_sensitive_key,
        redact_contract_mapping,
        redact_text_value,
    )

    print("\n\n 5.1 Redacting sensitive text and mappings")
    secret_text = "Standard request API_KEY=secret_key_12345 in header."
    redacted_text_out = redact_text_value(secret_text)
    print(f"Redacted Text: {redacted_text_out}")

    payload = {
        "user_id": "USER-A",
        "password": "my_super_secret_password",
        "api_key": "12345-abcde",
        "nested": {"secret": "inner_secret"},
    }
    redacted_map = redact_contract_mapping(payload)
    print(f"Redacted Mapping: {redacted_map}")

    print("\n\n 5.2 Key classification")
    print(f"Is 'password' sensitive? {is_sensitive_key('password')}")
    print(f"Is 'user_id' sensitive? {is_sensitive_key('user_id')}")

    assert True


def example_06_runtime_settings() -> None:
    """Demonstrate runtime configuration and settings loading."""
    print("\n" + "=" * 100)
    print("--- 6. Runtime Settings Example ---")
    print("=" * 100)

    from app.utils import load_settings

    print("\n\n 6.1 Loading active application settings")
    settings = load_settings()
    print(f"Loaded config environment: {settings.environment}")
    print(f"Runtime Profile: {settings.runtime_profile}")

    assert True


def example_07_dataframe_and_combinations() -> None:
    """Demonstrate serialization and JSON conversions."""
    print("\n--- 7. Serialization Demo ---")

    from app.utils import canonical_json, to_json_safe

    payload = {"symbol": "EURUSD", "period": 14, "threshold": Decimal("1.1000")}
    json_safe = to_json_safe(payload)
    canonical = canonical_json(json_safe)
    print(f"JSON safe representation: {json_safe}")
    print(f"Canonical JSON output: {canonical}")


def example_08_data_quality() -> None:
    """Demonstrate validation outcomes and reason codes."""
    print("\n--- 8. Validation Outcome Demo ---")

    from app.utils import build_validation_outcome, utc_now, validate_reason_code

    outcome = build_validation_outcome(
        verdict="PASS",
        check_id="chk_ohlcv_01",
        evaluated_at=utc_now(),
        reason_codes=["OHLCV.VALID"],
    )
    print(f"Validation Outcome: {outcome}")
    print(f"Reason code valid? {validate_reason_code('OHLCV.VALID')}")


def example_09_validations() -> None:
    """Demonstrate ID validation checks."""
    print("\n--- 9. Identity Validation Demo ---")

    from app.utils import generate_id, validate_id

    sample_id = generate_id("req")
    is_valid = validate_id(sample_id)
    print(f"Generated ID: '{sample_id}' (valid: {is_valid})")


def example_10_event_bus() -> None:
    """Demonstrate event envelope building and parsing."""
    print("\n--- 10. Event Envelope Demo ---")

    from app.utils import (
        build_event_envelope,
        generate_id,
        parse_event_envelope,
        utc_now,
    )

    envelope = build_event_envelope(
        event_id=generate_id("evt"),
        source_id="strategy_runner",
        source_sequence=1,
        correlation_id=generate_id("cor"),
        causation_id=None,
        deduplication_key="dedup_01",
        emitted_at=utc_now(),
        payload={"action": "BUY", "symbol": "EURUSD", "size": 0.1},
    )
    parsed = parse_event_envelope(envelope)
    print(f"Built & Parsed Envelope Event ID: {parsed['event_id']}")


def example_11_circuit_breakers_and_observability() -> None:
    """Demonstrate health state management."""
    print("\n--- 11. Health State Demo ---")

    from app.utils import build_health_state, parse_health_state, utc_now

    health = build_health_state(
        dependency="broker_adapter",
        category="TRANSIENT",
        state="DEGRADED",
        retryable=True,
        operator_action="RETRY",
        observed_at=utc_now(),
    )
    parsed = parse_health_state(health)
    print(f"Health State Status: {parsed['state']}")


def example_12_notifications() -> None:
    """Demonstrate notifications manager using app.utils exports."""
    print("\n--- 12. Notifications Router Demo ---")

    from app.utils import (
        build_notification_manager_config,
        create_notification_manager,
        get_notification_manager_status,
    )

    config = build_notification_manager_config(enabled=True)
    manager = create_notification_manager(config)
    status = get_notification_manager_status(manager)
    print(f"Notification Manager Status: {status}")


def example_13_paths() -> None:
    """Demonstrate safe parent directory creation."""
    print("\n--- 13. Safe Paths Demo ---")
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        target_file = Path(temp_dir) / "data" / "raw" / "EURUSD.csv"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with target_file.open("w") as f:
            f.write("timestamp,close\n2026-06-16T12:00:00Z,1.1000")

        assert target_file.exists()
        print(f"Verified safe paths creation for target file: '{target_file}'")


def example_14_auth() -> None:
    """Demonstrate auth context creation and validation."""
    print("\n--- 14. Auth Context Demo ---")

    from app.utils import (
        create_auth_context,
        generate_id,
        get_auth_context_type,
        utc_now,
    )

    context = create_auth_context(
        principal_id="agent-research-1",
        principal_type="SERVICE_ACCOUNT",
        roles=("researcher",),
        permissions=("read",),
        scopes=("utils",),
        tenant_or_environment="dev",
        request_id=generate_id("req"),
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        issued_at=utc_now(),
    )
    context_type = get_auth_context_type()
    print(
        f"Auth Context Principal: {context.principal_id}"
        f" (type: {context.principal_type}, schema: {context_type})"
    )


if __name__ == "__main__":
    print("==================================================")
    print("STARTING SHRED UTILITIES DEMO SCRIPT (01_utils.py)")
    print("==================================================")

    example_01_logger_example()
    example_02_error_handling_example()
    example_03_standard_tool_envelope_example()
    example_04_safe_path_normalization_example()
    example_05_security_and_redaction()
    example_06_runtime_settings()
    example_07_dataframe_and_combinations()
    example_08_data_quality()
    example_09_validations()
    example_10_event_bus()
    example_11_circuit_breakers_and_observability()
    example_12_notifications()
    example_13_paths()
    example_14_auth()

    print("==================================================")
    print("DEMO SCRIPT EXECUTED SUCCESSFULLY")
    print("==================================================")
