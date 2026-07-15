"""Redaction and secret-handling tests (NFR-BRK-007)."""

from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
)
from pydantic import SecretStr


def test_broker_error_details_redact_sensitive_keys() -> None:
    """Sensitive detail keys never survive into the constructed error."""
    error = BrokerError(
        code=BrokerErrorCode.BROKER_REQUEST_REJECTED,
        message="rejected",
        details={"password": "hunter2", "symbol": "EURUSD"},
    )
    assert error.details["password"] == "[REDACTED]"
    assert error.details["symbol"] == "EURUSD"


def test_connection_config_never_prints_plaintext_credentials() -> None:
    """String and repr forms of a config never leak a raw credential value."""
    config = BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=2,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        credentials={"password": SecretStr("super-secret-value")},
    )
    assert "super-secret-value" not in str(config)
    assert "super-secret-value" not in repr(config)
    assert config.credentials is not None
    assert config.credentials["password"].get_secret_value() == "super-secret-value"


def test_connection_config_rejects_empty_named_credentials() -> None:
    """Named credential values must be non-empty ``SecretStr`` instances."""
    import pytest

    with pytest.raises(ValueError, match="credentials require"):
        BrokerConnectionConfig(
            broker_id=BrokerId.MT5,
            environment=BrokerEnvironment.DEMO,
            provider_enabled=True,
            connect_timeout_sec=1,
            request_timeout_sec=1,
            transport_reconnect_max_attempts=0,
            stream_buffer_size=2,
            circuit_failure_threshold=2,
            circuit_recovery_timeout_sec=1,
            circuit_half_open_max_calls=1,
            credentials={"password": SecretStr("")},
        )
