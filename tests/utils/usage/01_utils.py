"""Usage example showing loguru logging in HaruQuantAI."""

import sys
from pathlib import Path

# Add project root to sys.path to allow direct execution
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import app  # noqa: F401


def example_01_logger() -> None:
    """Demonstrate how to log messages at various levels using loguru."""
    print("\n" + "=" * 100)
    print("--- 1. Logger Example ---")
    print("=" * 100)

    # 1. Standard structured logging levels
    # Import `logger` and use standard levels like
    # (`debug`, `info`, `warning`, `error`, `critical`).

    from app.utils import logger

    print("\n\n 1.1 Standard structured logging levels")
    logger.debug("This is a debug message containing developer details.")
    logger.info("This is an info message for standard application events.")
    logger.warning("This is a warning indicating a potential issue.")
    logger.error("This is an error indicating an execution failure.")
    logger.critical("This is a critical failure message.")

    # 2. Logging exceptions with tracebacks
    print("\n\n 1.2 Logging exceptions with tracebacks")
    # Use `logger.exception` inside an `except` block to log the traceback automatically
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        logger.exception("Successfully captured an exception with traceback:")

    # 3. Dynamic context logging using bind
    print("\n\n 1.3 Dynamic context logging using bind (Dynamic Contextual Metadata)")
    # Use .bind(...) to attach contextual fields like request IDs, users, IPs, etc.
    # These fields appear in the JSON log records automatically
    # in "request_id" and "user_id" fields.
    bound_logger = logger.bind(request_id="REQ-1002", user_id="USER-A")
    bound_logger.info("Processing order request with contextual metadata.")

    # 4. Routing to Specialized Log Files
    print("\n\n 1.4 Routing to Specialized Log Files")
    # Access/Auth specific logging (goes to access.log)
    access_logger = logger.bind(log_type="access", user_id="USER-A")
    access_logger.info("User logged in successfully from 192.168.1.50")
    # Debugging/Dev specific logging (goes to debug.log)

    # Assert that example completed cleanly
    assert True


def example_02_error_handling_example() -> None:
    """Demonstrate HaruQuant deterministic error utility patterns."""
    print("\n" + "=" * 100)
    print("--- 2. Error Handling Example ---")
    print("=" * 100)

    from app.utils import (
        ValidationError,
        code_for_exception,
        details_for_exception,
        error_name,
        exception_to_error_payload,
        normalize_error_code,
        route_error,
    )

    # 1. Raising typed error codes
    print("\n\n 2.1 Raising typed error codes")
    try:
        raise ValidationError("Input size exceeds limits.", code="INVALID_INPUT")  # noqa: TRY301
    except ValidationError as exc:
        print(f"Caught: {exc} (code: {exc.code})")

    # 2. Normalizing and looking up error metadata
    print("\n\n 2.2 Normalizing and looking up error metadata")
    normalized = normalize_error_code("invalid_input")
    print(f"Normalized 'invalid_input' -> {normalized}")
    print(f"Error Name: {error_name(normalized)}")

    # 4. Exception payload mapping helpers
    print("\n\n 2.4 Exception payload mapping helpers")
    raw_exc = ValueError("Invalid database format.")
    code = code_for_exception(raw_exc)
    details = details_for_exception(raw_exc)
    payload = exception_to_error_payload(raw_exc)
    print(f"Mapped ValueError -> code: {code}, details: {details}")
    print(f"Full payload: {payload}")

    # 5. Routing error events
    print("\n\n 2.5 Routing error events")
    route_result = route_error(
        ValidationError("Duplicate timestamp detected."),
        source="example_service",
    )
    print(f"Route Status: {route_result.status}")
    print(f"Route Key: {route_result.route_key}")

    assert True


def example_03_standard_tool_envelope_example() -> None:
    """Demonstrate Standard tool response envelopes and utility contracts."""
    print("\n" + "=" * 100)
    print("--- 3. Standard Tool Envelope Example ---")
    print("=" * 100)

    import time

    from app.utils import (
        build_metadata,
        canonical_json,
        error_response,
        response_from_exception,
        stable_identifier,
        success_response,
        validate_standard_response,
    )

    start = time.perf_counter()

    # 1. Building standard metadata
    print("\n\n 3.1 Building standard metadata")
    metadata = build_metadata(
        tool_name="example_calculator",
        start_time=start,
        tool_version="1.0.1",
        tool_category="math",
        tool_risk_level="low",
        reads=True,
    )
    print(f"Metadata execution_ms: {metadata['execution_ms']}")

    # 2. Generating a success response envelope
    print("\n\n 3.2 Generating a success response envelope")
    success = success_response(
        message="Calculation succeeded.",
        data={"result": 42.0},
        metadata=metadata,
    )
    validate_standard_response(success)
    print(f"Success Envelope: {success['status']}")

    # 3. Generating an error response envelope
    print("\n\n 3.3 Generating an error response envelope")
    error = error_response(
        message="Calculation failed.",
        code="INVALID_INPUT",
        details="Value must be positive.",
        metadata=metadata,
    )
    validate_standard_response(error)
    err_payload = error["error"]
    assert err_payload is not None
    print(f"Error Envelope: {error['status']} (code: {err_payload['code']})")

    # 4. Response mapping from a raw exception
    print("\n\n 3.4 Response mapping from a raw exception")
    try:
        raise ValueError("Division by zero in formula.")  # noqa: TRY301
    except ValueError as exc:
        mapped_error = response_from_exception(exception=exc, metadata=metadata)
        validate_standard_response(mapped_error)
        print(f"Exception Mapped Envelope Status: {mapped_error['status']}")

    # 5. Stable identifiers and canonical JSON
    print("\n\n 3.5 Stable identifiers and canonical JSON")
    payload = {"symbol": "EURUSD", "period": 14, "mode": "strict"}
    canonical = canonical_json(payload)
    fingerprint = stable_identifier(payload, prefix="run")
    print(f"Canonical JSON: {canonical}")
    print(f"Fingerprint ID: {fingerprint}")

    assert True


def example_05_security_and_redaction() -> None:
    """Demonstrate security helpers for redaction, hashing, and encryption."""
    print("\n" + "=" * 100)
    print("--- 5. Security and Redaction Example ---")
    print("=" * 100)

    from app.utils import (
        classify_secret_key,
        decrypt_text,
        encrypt_text,
        generate_encryption_key,
        hash_password,
        redact_mapping,
        redact_text,
        select_active_secret_version,
        verify_password,
    )

    # 1. Redacting sensitive text and mappings
    print("\n\n 5.1 Redacting sensitive text and mappings")
    secret_text = "Standard request API_KEY=secret_key_12345 in header."
    redacted_text_out = redact_text(secret_text)
    print(f"Redacted Text: {redacted_text_out}")

    payload = {
        "user_id": "USER-A",
        "password": "my_super_secret_password",
        "api_key": "12345-abcde",
        "nested": {"secret": "inner_secret"},
    }
    redacted_map = redact_mapping(payload)
    print(f"Redacted Mapping: {redacted_map}")

    # 2. Key classification
    print("\n\n 5.2 Key classification")
    print(f"Is 'password' sensitive? {classify_secret_key('password')}")
    print(f"Is 'user_id' sensitive? {classify_secret_key('user_id')}")

    # 3. Password hashing and verification
    print("\n\n 5.3 Password hashing and verification")
    hashed = hash_password("my_secure_password")
    print(f"Hashed password format: {hashed[:30]}...")
    matched = verify_password("my_secure_password", hashed)
    print(f"Password matched: {matched}")

    # 4. Fernet symmetric encryption and decryption
    print("\n\n 5.4 Fernet symmetric encryption and decryption")
    key = generate_encryption_key()
    ciphertext = encrypt_text("Sensitive trading strategy parameters", key=key)
    print(f"Ciphertext: {ciphertext[:30]}...")
    decrypted = decrypt_text(ciphertext, key=key)
    print(f"Decrypted text: {decrypted}")

    # 5. Selecting active secret versions
    print("\n\n 5.5 Selecting active secret versions")
    secret_versions = {
        "v1": {"version": 1, "active": True, "value": "old_key"},
        "v2": {"version": 2, "active": True, "value": "current_key"},
        "v3": {"version": 3, "active": False, "value": "future_key"},
    }
    active_secret = select_active_secret_version(secret_versions)
    print(f"Selected highest active version: {active_secret['version']}")

    assert True


def example_06_runtime_settings() -> None:
    """Demonstrate runtime configuration and settings loading using Pydantic."""
    print("\n" + "=" * 100)
    print("--- 6. Runtime Settings Example ---")
    print("=" * 100)

    from app.utils import (
        create_config,
        load_config,
        validate_config,
    )

    # 1. Loading active application configuration
    print("\n\n 6.1 Loading active application configuration")
    cfg = load_config()
    print(f"Loaded config environment: {cfg.environment}")
    print(f"App Name: {cfg.app_name}")
    print(f"Log Level: {cfg.log_level}")
    print(f"Strict Validation: {cfg.strict_validation}")

    # 2. Live trading environment constraints
    print("\n\n 6.2 Live trading environment constraints")
    print(f"Live Trading Enabled? {cfg.live_enabled}")
    print(f"Live Trading Mode: {cfg.live_mode}")
    print(f"Workflow Timeout: {cfg.live_workflow_timeout_seconds}s")
    print(f"Max Snapshot Staleness: {cfg.live_max_staleness_seconds}s")

    # 3. Validating settings for live deployment
    print("\n\n 6.3 Validating settings for live deployment")
    errors = validate_config(cfg)
    if errors:
        print(f"Config validation warnings/errors: {errors}")
    else:
        print("Config is valid for live runtime deployment.")

    # 4. Constructing EdgeLab research configuration
    print("\n\n 6.4 Constructing EdgeLab research configuration")
    research_cfg = create_config()
    print(f"EdgeLab Data Source: {research_cfg.data_config.source}")
    print(f"Mean Reversion horizon: {research_cfg.mean_reversion_config.fade_horizon}")

    assert True


def example_07_dataframe_and_combinations() -> None:
    """Demonstrate lazy alignment, data mapping, and grid parameter combinatorics."""
    print("\n--- 7. DataFrames & Combinations Demo ---")
    import pandas as pd
    from app.services.data.dataframe_tools import (
        align_dataframe_datetime,
        parameter_combinations,
        serialize_dataframe_records,
    )

    # Parameter grid optimization helpers
    grid = {
        "fast_ema": [5, 10],
        "slow_ema": [20, 30],
    }
    combinations = parameter_combinations(grid)
    print(f"Parameter combinations for grid: {combinations}")

    # DataFrame alignment and conversion
    df = pd.DataFrame(
        [
            {"timestamp": "2026-06-16 10:00:00", "close": 1.1000},
            {"timestamp": "2026-06-16 10:01:00", "close": 1.1005},
        ]
    )
    aligned_df = align_dataframe_datetime(df, timestamp_column="timestamp")
    records = serialize_dataframe_records(aligned_df)
    print("Serialized records:", records)


def example_08_data_quality() -> None:
    """Demonstrate bar checks, volume checks, and data profiles creation."""
    print("\n--- 8. Data Quality Checking Demo ---")
    from typing import Any, cast

    import pandas as pd
    from app.services.data.data_quality import (
        inspect_ohlcv_quality,
        validate_ohlcv_quality,
    )

    records = [
        {
            "timestamp": "2026-06-16T10:00:00Z",
            "open": 1.10,
            "high": 1.11,
            "low": 1.09,
            "close": 1.10,
            "volume": 100,
        },
        {
            "timestamp": "2026-06-16T10:01:00Z",
            "open": 1.10,
            "high": 1.12,
            "low": 1.08,
            "close": 1.11,
            "volume": 200,
        },
    ]

    df = pd.DataFrame(records)
    res = inspect_ohlcv_quality(df)
    issues = cast("list[Any]", res.get("issues", []))
    print(f"Data Quality Profiles: Passed={res['passed']}, Issues Count={len(issues)}")
    resp = validate_ohlcv_quality(df)
    print("Validate OHLCV Quality response status:", resp["status"])


def example_12_notifications() -> None:
    """Demonstrate real notifications using settings credentials."""
    print("\n--- 12. Notifications Router Demo (Real Adapters) ---")
    from app.utils import (
        DesktopNotificationAdapter,
        EmailNotificationAdapter,
        NotificationRouter,
        TelegramNotificationAdapter,
        load_config,
        route_notification,
    )

    settings = load_config()
    from app.utils.notifications import NotificationAdapter, NotificationChannel

    adapters: dict[NotificationChannel, NotificationAdapter] = {
        "desktop": DesktopNotificationAdapter(),
        "telegram": TelegramNotificationAdapter(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
        ),
        "email": EmailNotificationAdapter(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            recipient=settings.smtp_recipient or settings.smtp_username,
        ),
    }
    router = NotificationRouter(adapters=adapters)

    # 1. Desktop Notification
    print("Sending real Desktop notification...")
    res_desktop = route_notification(
        router,
        channel="desktop",
        title="HaruQuant Desktop Alert",
        body="This is a real desktop notification from the utilities demo.",
    )
    print(
        f"Desktop Result: status={res_desktop.status}, "
        f"channel={res_desktop.channel}, provider={res_desktop.provider}"
    )

    # 2. Telegram Notification
    if settings.telegram_bot_token and settings.telegram_chat_id:
        print("Sending real Telegram notification...")
        res_telegram = route_notification(
            router,
            channel="telegram",
            title="HaruQuant Telegram Alert",
            body="This is a real Telegram notification from the utilities demo.",
        )
        print(
            f"Telegram Result: status={res_telegram.status}, "
            f"channel={res_telegram.channel}, provider={res_telegram.provider}"
        )
    else:
        print("Skipping Telegram (not configured in settings/env).")

    # 3. Email Notification
    if settings.smtp_username and settings.smtp_password:
        print("Sending real Email notification...")
        res_email = route_notification(
            router,
            channel="email",
            title="HaruQuant Email Alert",
            body="This is a real Email notification from the utilities demo.",
        )
        print(
            f"Email Result: status={res_email.status}, "
            f"channel={res_email.channel}, provider={res_email.provider}"
        )
    else:
        print("Skipping Email (not configured in settings/env).")


if __name__ == "__main__":
    print("==================================================")
    print("STARTING SHRED UTILITIES DEMO SCRIPT (01_utils.py)")
    print("==================================================")

    example_01_logger()
    # example_02_error_handling_example()
    # example_03_standard_tool_envelope_example()
    # example_05_security_and_redaction()
    example_06_runtime_settings()
    # example_07_dataframe_and_combinations()
    # example_08_data_quality()
    # example_12_notifications()

    print("==================================================")
    print("DEMO SCRIPT EXECUTED SUCCESSFULLY")
    print("==================================================")
