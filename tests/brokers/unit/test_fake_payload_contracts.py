"""Validate operation-specific FakeBrokerAdapter success payloads."""

import pytest
from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.testing import FakeBrokerAdapter
from pydantic import SecretStr


def _config() -> BrokerConnectionConfig:
    """Return one bounded fake configuration."""
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=4,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference="1",
        credentials={
            "login": SecretStr("1"),
            "password": SecretStr("x"),
            "server": SecretStr("Demo"),
        },
    )


@pytest.mark.parametrize(
    ("operation", "fixture"),
    [
        (BrokerCapabilityId.PLACE_ORDER, object()),
        (BrokerCapabilityId.GET_QUOTE, None),
        (BrokerCapabilityId.SUBSCRIBE_QUOTES, ("EURUSD", 1)),
    ],
)
def test_fake_rejects_wrong_payload_category(
    operation: BrokerCapabilityId,
    fixture: object,
) -> None:
    """Reject a fixture before it can produce a malformed result."""
    with pytest.raises(TypeError):
        FakeBrokerAdapter(_config(), fixtures={operation: fixture})
