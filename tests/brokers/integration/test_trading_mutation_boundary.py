"""WF-BRK-004: submit one broker mutation (Trading-only capability)."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from app.services.brokers import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerError,
    BrokerErrorCode,
    BrokerId,
    BrokerOrder,
)
from app.services.brokers.testing import FakeBrokerAdapter


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
    )


def _capabilities() -> dict[BrokerCapabilityId, BrokerCapability]:
    return {
        operation: BrokerCapability(
            capability=operation,
            implementation_status="IMPLEMENTED",
            availability="AVAILABLE",
            access_mode="WRITE",
            requirement="PERMISSION",
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
        result = await adapter.place_order(object())
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
        result = await adapter.place_order(object())
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
        result = await adapter.place_order(object())
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_UNKNOWN_OUTCOME
        assert result.error.retryable is False

    asyncio.run(exercise())
