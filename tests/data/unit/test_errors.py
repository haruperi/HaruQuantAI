"""Unit tests for deterministic Data errors."""

from app.services.data.contracts import DATA_ERROR_MANIFEST, DataError


def test_data_error_redacts_sensitive_details() -> None:
    """Sensitive keys and values are redacted before crossing a boundary."""
    redacted = DataError("NETWORK_ERROR", safe_details={"api_token": "secret"})
    assert redacted.safe_details == {"api_token": "[REDACTED]"}
    error = DataError("NOT_A_CODE", safe_details={"operation": "read"})
    assert error.code == "UNKNOWN_ERROR"
    assert "read" not in str(error)


def test_error_manifest_is_complete_and_unique() -> None:
    """The manifest contains exactly the authoritative deterministic codes."""
    expected = {
        "AUTHENTICATION_FAILED",
        "BUFFER_OVERFLOW",
        "CHECKPOINT_CORRUPTED",
        "CIRCUIT_BREAKER_OPEN",
        "CONCURRENT_WRITE_LOCKED",
        "CREDENTIALS_MISSING",
        "DATABASE_ERROR",
        "DATA_DROPPED",
        "DATA_NOT_FOUND",
        "DATA_QUALITY_FAILED",
        "DB_CONNECTION_ERROR",
        "DB_WRITE_FAILED",
        "EMPTY_RESULT",
        "FEED_HEARTBEAT_TIMEOUT",
        "FILE_CORRUPTED",
        "INVALID_INPUT",
        "JOB_NOT_FOUND",
        "LICENSE_RESTRICTION",
        "LIMIT_EXCEEDED",
        "MISSING_ASSET_METADATA",
        "NETWORK_ERROR",
        "PERMISSION_DENIED",
        "POLICY_BLOCKED",
        "PRECISION_MISMATCH",
        "SCHEDULER_ERROR",
        "SCHEMA_MIGRATION_FAILED",
        "SERVICE_UNAVAILABLE",
        "SOURCE_UNAVAILABLE",
        "STALE_EVIDENCE",
        "STATE_RECOVERY_FAILED",
        "TIMEOUT",
        "UNKNOWN_ERROR",
        "UNSUPPORTED_OPERATION",
        "UNSUPPORTED_SOURCE",
        "UNSUPPORTED_TIMEFRAME",
        "VALIDATION_FAILED",
    }
    assert set(DATA_ERROR_MANIFEST) == expected
    assert all(key == value.code for key, value in DATA_ERROR_MANIFEST.items())
