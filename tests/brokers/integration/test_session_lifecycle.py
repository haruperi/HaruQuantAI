"""WF-BRK-002: connect/authenticate/disconnect session lifecycle.

The workflow is exercised through the genuine `MT5BrokerAdapter` over an
injected deterministic transport, so connection-only validation, provider
authentication, account/environment verification, capability refresh, state
events, idempotent release, and context-manager cleanup all execute for real.
Only the provider socket is substituted.
"""

import asyncio
from datetime import UTC, datetime

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.mt5.adapter import MT5BrokerAdapter
from pydantic import SecretStr

_LOGIN = "12345"
_SERVER = "Demo-Server"


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=BrokerEnvironment.DEMO,
        provider_enabled=True,
        connect_timeout_sec=1,
        request_timeout_sec=1,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=8,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1,
        circuit_half_open_max_calls=1,
        account_reference=_LOGIN,
        credentials={
            "login": SecretStr(_LOGIN),
            "password": SecretStr("offline-placeholder"),
            "server": SecretStr(_SERVER),
        },
    )


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


class _StubTransport:
    """Deterministic MT5 terminal stub recording every provider call."""

    def __init__(self, *, verified: bool = True) -> None:
        self._verified = verified
        self.calls: list[str] = []
        self.connected = False
        self.closed = False

    async def connect(self) -> bool:
        self.connected = True
        self.calls.append("initialize")
        return self._verified

    async def call(self, name: str, *args: object, **kwargs: object) -> object:
        del args, kwargs
        self.calls.append(name)
        now = datetime(2026, 1, 1, tzinfo=UTC).timestamp()
        if name == "terminal_info":
            return (
                {"connected": True, "trade_allowed": True} if self._verified else None
            )
        if name == "account_info":
            return {
                "login": int(_LOGIN),
                "server": _SERVER,
                "currency": "USD",
                "balance": 1000,
                "equity": 1000,
                "margin": 0,
                "margin_free": 1000,
                "trade_allowed": True,
            }
        if name == "version":
            return "5.0.0"
        if name == "symbol_info_tick":
            return {"time": now, "bid": 1.1, "ask": 1.1002, "last": 1.1001}
        return None

    async def constant(self, name: str) -> object:
        self.calls.append(f"constant:{name}")
        return 0

    async def close(self) -> None:
        self.calls.append("shutdown")
        self.closed = True
        self.connected = False


def test_session_lifecycle_verifies_and_cleans_up() -> None:
    """Connect verifies a session; disconnect deterministically releases it."""
    transport = _StubTransport()
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        connected = await adapter.connect()
        assert connected.is_success, connected.error
        # The session is established through the provider transport, not a flag.
        assert transport.connected
        assert "initialize" in transport.calls
        # Account and environment identity are verified against provider truth.
        assert "account_info" in transport.calls

        status = await adapter.get_connection_status()
        assert status.data is not None
        assert status.data.state == BrokerConnectionState.READY
        assert status.data.transport_connected

        flags = await adapter.get_feature_flags()
        assert flags.data is not None
        assert set(flags.data.capabilities) == set(BrokerCapabilityId)

        disconnected = await adapter.disconnect()
        assert disconnected.is_success
        assert transport.closed
        final_status = await adapter.get_connection_status()
        assert final_status.data is not None
        assert final_status.data.state == BrokerConnectionState.DISCONNECTED

        # Idempotent disconnect never errors.
        again = await adapter.disconnect()
        assert again.is_success

    asyncio.run(exercise())


def test_session_lifecycle_supports_async_context_manager() -> None:
    """The adapter's async context manager connects and always disconnects."""

    async def exercise() -> BrokerConnectionState:
        transport = _StubTransport()
        adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)
        async with adapter:
            status = await adapter.get_connection_status()
            assert status.data is not None
            assert status.data.state == BrokerConnectionState.READY
        assert transport.closed
        final_status = await adapter.get_connection_status()
        assert final_status.data is not None
        return final_status.data.state

    assert asyncio.run(exercise()) == BrokerConnectionState.DISCONNECTED


def test_connect_emits_one_event_per_validated_transition() -> None:
    """Every validated lifecycle transition yields a canonical event."""
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=_StubTransport())

    async def exercise() -> list[BrokerConnectionState]:
        assert (await adapter.connect()).is_success
        states: list[BrokerConnectionState] = []
        events = adapter.connection_events()
        for _ in range(2):
            try:
                event = await asyncio.wait_for(anext(events), timeout=0.5)
            except (TimeoutError, StopAsyncIteration):
                break
            states.append(event.new_state)
        return states

    observed = asyncio.run(exercise())
    assert BrokerConnectionState.CONNECTING in observed
    assert BrokerConnectionState.READY in observed


def test_unverified_account_fails_closed_without_reporting_success() -> None:
    """A failed verification never returns success (README known-defect guard)."""
    transport = _StubTransport(verified=False)
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        result = await adapter.connect()
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CONNECTION_FAILED
        status = await adapter.get_connection_status()
        assert status.data is not None
        assert status.data.state == BrokerConnectionState.FAILED

    asyncio.run(exercise())
