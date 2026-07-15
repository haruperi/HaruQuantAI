"""cTrader adapter tests using an injected fake transport."""

import asyncio

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)
from app.services.brokers.ctrader.adapter import CTraderBrokerAdapter
from pydantic import SecretStr


def _config(**overrides: object) -> BrokerConnectionConfig:
    values: dict[str, object] = {
        "broker_id": BrokerId.CTRADER,
        "environment": BrokerEnvironment.DEMO,
        "provider_enabled": True,
        "connect_timeout_sec": 1,
        "request_timeout_sec": 1,
        "transport_reconnect_max_attempts": 0,
        "stream_buffer_size": 2,
        "circuit_failure_threshold": 2,
        "circuit_recovery_timeout_sec": 1,
        "circuit_half_open_max_calls": 1,
        "account_reference": "998877",
        "credentials": {
            "client_id": SecretStr("client-id"),
            "client_secret": SecretStr("client-secret"),
            "access_token": SecretStr("access-token"),
            "account_id": SecretStr("998877"),
        },
    }
    values.update(overrides)
    return BrokerConnectionConfig(**values)  # type: ignore[arg-type]


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


class _FakeTransport:
    def __init__(self, *, verified: bool = True) -> None:
        self._verified = verified
        self.closed = False

    async def connect(self) -> bool:
        return self._verified

    async def close(self) -> None:
        self.closed = True


def test_adapter_requires_matching_account_reference() -> None:
    """The declared account reference must match the resolved account_id."""
    with pytest.raises(ValueError, match="account_reference must match account_id"):
        CTraderBrokerAdapter(_config(account_reference="000000"), _capabilities())


def test_adapter_rejects_incomplete_credentials() -> None:
    """Every required cTrader credential must be present."""
    with pytest.raises(ValueError, match="resolved cTrader credentials are incomplete"):
        CTraderBrokerAdapter(
            _config(
                credentials={"client_id": SecretStr("client-id")},
                account_reference=None,
            ),
            _capabilities(),
        )


def test_adapter_connect_succeeds_on_verified_transport() -> None:
    """A verified transport session transitions the adapter to ready."""
    adapter = CTraderBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=True)
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert result.is_success

    asyncio.run(exercise())


def test_adapter_connect_fails_closed_without_authentication() -> None:
    """An unauthenticated transport never reports a successful connection."""
    adapter = CTraderBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=False)
    )

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success
        assert result.error is not None

    asyncio.run(exercise())


def test_adapter_disconnect_releases_transport() -> None:
    """Disconnecting releases the owned cTrader session transport."""
    transport = _FakeTransport(verified=True)
    adapter = CTraderBrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        await adapter.connect()
        await adapter.disconnect()

    asyncio.run(exercise())
    assert transport.closed


def test_adapter_platform_info_reports_environment_endpoint() -> None:
    """Platform info reports the exact demo/live endpoint without secrets."""
    adapter = CTraderBrokerAdapter(
        _config(), _capabilities(), transport=_FakeTransport(verified=True)
    )

    async def exercise() -> None:
        result = await adapter.get_platform_info()
        assert result.data is not None
        assert result.data.endpoint_metadata["endpoint"] == "demo.ctraderapi.com:5035"

    asyncio.run(exercise())
