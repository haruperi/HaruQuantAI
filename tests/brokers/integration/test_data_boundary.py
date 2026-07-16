"""WF-BRK-003: Data receives direct provider truth via read capabilities."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from app.services.brokers import (
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
    BrokerPage,
)
from app.services.brokers.testing import FakeBrokerAdapter


def _config() -> BrokerConnectionConfig:
    return BrokerConnectionConfig(
        broker_id=BrokerId.YAHOO,
        environment=BrokerEnvironment.SANDBOX,
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
            access_mode="READ",
            requirement="NONE",
            verification_status="NOT_TESTED",
            execution_model="TEST_DOUBLE",
        )
        for operation in BrokerCapabilityId
    }


def test_data_receives_provider_truth_without_normalization() -> None:
    """Data (an emulated read-only caller) receives the exact provider page."""
    bar = BrokerBar(
        symbol="AAPL",
        opening_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        closing_timestamp=datetime(2026, 1, 2, tzinfo=UTC),
        is_closed=True,
        open=Decimal(150),
        high=Decimal(152),
        low=Decimal(149),
        close=Decimal(151),
        provider_timeframe="1d",
        requested_timeframe="1d",
        price_unit="provider_quote_currency",
        quantity_unit="provider_volume",
    )
    page = BrokerPage(items=(bar,), limit=1)
    adapter = FakeBrokerAdapter(
        _config(),
        _capabilities(),
        fixtures={BrokerCapabilityId.GET_HISTORICAL_BARS: page},
    )

    async def exercise() -> None:
        await adapter.connect()
        result = await adapter.get_historical_bars("AAPL", "1d", limit=1)
        assert result.data is page
        assert result.data.items[0] is bar

    asyncio.run(exercise())


def test_unsupported_observation_never_calls_provider() -> None:
    """A read capability with no registered fixture returns unsupported."""
    adapter = FakeBrokerAdapter(_config(), _capabilities())

    async def exercise() -> None:
        result = await adapter.get_order_book("AAPL")
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())
