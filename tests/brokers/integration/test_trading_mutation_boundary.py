"""WF-BRK-004: submit one broker mutation (Trading-only capability)."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerOrder,
    BrokerOrderRequest,
    create_broker_adapter,
)
from app.services.brokers.mt5.adapter import MT5BrokerAdapter
from app.services.brokers.testing import FakeBrokerAdapter
from pydantic import SecretStr


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
        account_reference="100001",
        credentials={
            "login": SecretStr("100001"),
            "password": SecretStr("offline-placeholder"),
            "server": SecretStr("Offline-Demo"),
        },
    )


_MUTATIONS = {
    BrokerCapabilityId.CHECK_ORDER,
    BrokerCapabilityId.PLACE_ORDER,
    BrokerCapabilityId.MODIFY_ORDER,
    BrokerCapabilityId.CANCEL_ORDER,
    BrokerCapabilityId.MODIFY_POSITION,
    BrokerCapabilityId.CLOSE_POSITION,
}


def _order_request() -> BrokerOrderRequest:
    """Build one complete, structurally valid V1 order request.

    Returns:
        A canonical order request accepted by the V1 field manifest.
    """
    return BrokerOrderRequest(
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity=Decimal("0.01"),
        quantity_unit="lots",
        environment=BrokerEnvironment.DEMO,
        client_request_id="req-2f1d5a6c-8b3e-4c17-9f52-70a1c8d94e33",
    )


class _RecordingTransport:
    """Genuine-shaped MT5 terminal stub recording every provider call."""

    def __init__(self, *, fail_order_send: BaseException | None = None) -> None:
        self._fail_order_send = fail_order_send
        self.calls: list[str] = []
        self.closed = False

    async def connect(self) -> bool:
        self.calls.append("initialize")
        return True

    async def call(self, name: str, *args: object, **kwargs: object) -> object:
        del args, kwargs
        self.calls.append(name)
        if name == "terminal_info":
            return {"connected": True, "trade_allowed": True}
        if name == "account_info":
            return {
                "login": 100001,
                "server": "Offline-Demo",
                "currency": "USD",
                "balance": 1000,
                "equity": 1000,
                "margin": 0,
                "margin_free": 1000,
                "trade_allowed": True,
            }
        if name == "order_send":
            if self._fail_order_send is not None:
                raise self._fail_order_send
            return {"retcode": 10009, "order": 1, "deal": 2, "volume": 0.01}
        return None

    async def constant(self, name: str) -> object:
        self.calls.append(f"constant:{name}")
        return 0

    async def close(self) -> None:
        self.closed = True


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    """Declare only the mutation set as WRITE, mirroring the real catalogue.

    Returns:
        A complete capability map for the emulated Trading caller.
    """
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="WRITE" if operation in _MUTATIONS else "READ",
            requirement="PERMISSION" if operation in _MUTATIONS else "NONE",
            verification_status="TESTED_SANDBOX",
            execution_model="TEST_DOUBLE",
            verification_evidence=(
                "tests/brokers/integration/test_trading_mutation_boundary.py",
            ),
            release_approval_reference="test-double-approval",
        )
        for operation in BrokerCapabilityId
    }


def test_mutation_returns_provider_acknowledgement_without_retry() -> None:
    """A single approved mutation returns direct provider truth, once."""
    order = BrokerOrder(
        order_id="order-1",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        state="FILLED",
        quantity=Decimal(1),
        filled=Decimal(1),
        remaining=Decimal(0),
        quantity_unit="lots",
        retrieved_at=datetime.now(UTC),
    )
    adapter = FakeBrokerAdapter(
        _config(),
        _capabilities(),
        fixtures={BrokerCapabilityId.PLACE_ORDER: order},
    )
    calls: list[BrokerCapabilityId] = []
    original_invoke = adapter._invoke

    async def _tracking_invoke(operation: BrokerCapabilityId) -> object:
        calls.append(operation)
        return await original_invoke(operation)

    adapter._invoke = _tracking_invoke  # type: ignore[method-assign]

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.place_order(_order_request())
        assert result.data is order

    asyncio.run(exercise())
    assert calls.count(BrokerCapabilityId.PLACE_ORDER) == 1


def test_mutation_rejection_carries_redacted_provider_evidence() -> None:
    """A rejected mutation returns the exact structured provider evidence."""
    adapter = FakeBrokerAdapter(_config(), _capabilities())
    adapter.inject_error(
        BrokerCapabilityId.PLACE_ORDER,
        BrokerError(
            code=BrokerErrorCode.BROKER_REQUEST_REJECTED,
            message="rejected",
            provider_code="10004",
        ),
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.place_order(_order_request())
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_REJECTED
        assert result.error.provider_code == "10004"

    asyncio.run(exercise())


def test_unknown_mutation_outcome_is_never_treated_as_success() -> None:
    """A possible-transmission-without-acknowledgement never reports success."""
    adapter = FakeBrokerAdapter(_config(), _capabilities())
    adapter.inject_error(
        BrokerCapabilityId.PLACE_ORDER,
        BrokerError(
            code=BrokerErrorCode.BROKER_UNKNOWN_OUTCOME,
            message="uncertain",
            retryable=False,
        ),
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.place_order(_order_request())
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_UNKNOWN_OUTCOME
        assert result.error.retryable is False

    asyncio.run(exercise())


def test_structurally_invalid_request_is_rejected_before_transmission() -> None:
    """An incomplete request never reaches the provider (WF-BRK-004 step 1)."""
    with pytest.raises(ValueError, match="quantity must be positive"):
        BrokerOrderRequest(
            symbol="EURUSD",
            side="BUY",
            order_type="MARKET",
            quantity=Decimal(0),
            quantity_unit="lots",
            environment=BrokerEnvironment.DEMO,
        )


def test_real_adapter_rejects_an_unresolvable_target_without_transmitting() -> None:
    """The genuine MT5 adapter validates before any mutation is transmitted."""
    transport = _RecordingTransport()
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        result = await adapter.cancel_order("not-a-ticket")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_REQUEST_INVALID

    asyncio.run(exercise())
    assert "order_send" not in transport.calls


def test_real_adapter_reports_unknown_outcome_after_possible_transmission() -> None:
    """A failure at or after transmission never claims the order was not sent."""
    transport = _RecordingTransport(fail_order_send=RuntimeError("socket reset"))
    adapter = MT5BrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        assert (await adapter.connect()).is_success
        result = await adapter.place_order(_order_request())
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_UNKNOWN_OUTCOME
        assert result.error.retryable is False

    asyncio.run(exercise())
    # The mutation is attempted exactly once and is never replayed.
    assert transport.calls.count("order_send") == 1


def test_registry_created_real_adapter_blocks_every_unreleased_write() -> None:
    """The genuine registry/MT5 boundary blocks writes before provider access."""
    created = create_broker_adapter(BrokerId.MT5, _config())
    assert created.data is not None
    request = _order_request()

    async def exercise() -> None:
        result = await created.data.place_order(request)
        assert result.error is not None
        assert result.error.code is BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())
