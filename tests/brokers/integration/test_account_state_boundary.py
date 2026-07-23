"""WF-BRK-005: read account and execution state.

The workflow runs through the genuine `MT5BrokerAdapter` over an injected
deterministic transport returning raw provider payloads, so the canonical
account, position, and order DTOs are produced by `mt5/mapping.py` itself. A
regression in that mapping fails this workflow.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerPositionFilter,
)
from app.services.brokers.mt5.adapter import MT5BrokerAdapter
from pydantic import SecretStr

_LOGIN = "12345"
_SERVER = "Demo-Server"
_NOW = datetime(2026, 1, 1, tzinfo=UTC)


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
    """Deterministic MT5 terminal stub returning raw provider payloads."""

    def __init__(self, *, positions: tuple[object, ...] | None = None) -> None:
        self._positions = positions
        self.calls: list[str] = []
        self.closed = False

    async def connect(self) -> bool:
        self.calls.append("initialize")
        return True

    async def call(self, name: str, *args: object, **kwargs: object) -> object:
        del args, kwargs
        self.calls.append(name)
        stamp = _NOW.timestamp()
        if name == "terminal_info":
            return {"connected": True, "trade_allowed": True}
        if name == "account_info":
            return {
                "login": int(_LOGIN),
                "server": _SERVER,
                "currency": "USD",
                "balance": "1000.55",
                "equity": "1100.25",
                "margin": "100.10",
                "margin_free": "1000.15",
                "trade_allowed": True,
            }
        if name == "version":
            return "5.0.0"
        if name == "positions_get":
            if self._positions is not None:
                return self._positions
            return (
                {
                    "ticket": 987654321,
                    "symbol": "EURUSD",
                    "type": 0,
                    "volume": "1.5",
                    "price_open": "1.10500",
                    "price_current": "1.20500",
                    "profit": "150.25",
                    "time_update": stamp,
                },
            )
        return None

    async def constant(self, name: str) -> object:
        self.calls.append(f"constant:{name}")
        return 0

    async def close(self) -> None:
        self.closed = True


def test_account_state_preserves_provider_ids_and_bounds() -> None:
    """Account reads preserve the exact provider account ID and redaction."""
    transport = _StubTransport()
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        result = await adapter.get_account_info()
        assert result.is_success, result.error
        account = result.data
        assert account is not None

        # Provider identity and financials are mapped, never fabricated.
        assert account.account_id == _LOGIN
        assert account.balance == Decimal("1000.55")
        assert account.equity == Decimal("1100.25")
        assert account.currency == "USD"

        # The full account identifier never appears unredacted.
        assert account.account_reference_redacted is not None
        assert account.account_reference_redacted != _LOGIN

        # Both provider and retrieval times are present; freshness is the
        # caller's decision, not the adapter's.
        assert account.retrieved_at.tzinfo is not None
        assert "account_info" in transport.calls

    asyncio.run(exercise())


def test_execution_state_preserves_exact_provider_identifiers() -> None:
    """Position reads preserve the exact provider ticket and P&L values."""
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=_StubTransport())

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        result = await adapter.get_positions(BrokerPositionFilter(), limit=10)
        assert result.is_success, result.error
        page = result.data
        assert page is not None
        assert page.returned_count == 1
        position = page.items[0]
        assert position.position_id == "987654321"
        assert position.symbol == "EURUSD"
        assert position.quantity == Decimal("1.5")
        assert position.profit == Decimal("150.25")
        # Bounds are explicit; no unbounded whole-history retrieval occurred.
        assert page.limit == 10
        assert page.truncated is False

    asyncio.run(exercise())


def test_empty_provider_page_is_a_success_not_an_error() -> None:
    """A valid empty provider page is a successful empty page."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_StubTransport(positions=())
    )

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        result = await adapter.get_positions(BrokerPositionFilter(), limit=10)
        assert result.is_success, result.error
        assert result.data is not None
        assert result.data.items == ()
        assert result.data.returned_count == 0

    asyncio.run(exercise())


def test_missing_account_target_returns_exact_not_found_code() -> None:
    """A missing provider target returns the exact BROKER_*_NOT_FOUND result."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_StubTransport(positions=())
    )

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        result = await adapter.get_position("999999999")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_POSITION_NOT_FOUND

    asyncio.run(exercise())


def test_structurally_invalid_target_is_distinct_from_not_found() -> None:
    """A malformed caller identifier is a request error, not a missing target."""
    adapter = MT5BrokerAdapter(
        _config(), _capabilities(), transport=_StubTransport(positions=())
    )

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        result = await adapter.get_position("not-a-ticket")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID

    asyncio.run(exercise())
