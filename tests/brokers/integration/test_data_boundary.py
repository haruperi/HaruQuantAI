"""WF-BRK-003: Data receives direct provider truth via read capabilities.

The workflow runs through the genuine `YahooBrokerAdapter` over an injected
deterministic transport that returns a raw provider table. The canonical page is
therefore produced by the domain's own mapping, not supplied by the test, so a
regression in `yahoo/mapping.py` fails this workflow.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers import (
    BrokerBar,
    BrokerCapability,
    BrokerCapabilityId,
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.yahoo.adapter import YahooBrokerAdapter

_SYMBOL = "AAPL"
_OPENED_AT = datetime(2026, 1, 1, tzinfo=UTC)


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
        probe_symbol=_SYMBOL,
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


class _Table:
    """Minimal stand-in for the public yfinance table iteration surface."""

    def __init__(self, rows: list[tuple[datetime, dict[str, object]]]) -> None:
        self._rows = rows

    def iterrows(self) -> object:
        return iter(self._rows)


class _StubTransport:
    """Return one raw provider table and record the exact requested symbol."""

    def __init__(self, table: object) -> None:
        self._table = table
        self.requested: list[tuple[str, str]] = []

    async def history(
        self, *, symbol: str, timeframe: str, start: object, end: object
    ) -> object:
        del start, end
        self.requested.append((symbol, timeframe))
        return self._table


def _provider_table() -> _Table:
    return _Table(
        [
            (
                _OPENED_AT,
                {
                    "Open": "150.25",
                    "High": "152.50",
                    "Low": "149.75",
                    "Close": "151.00",
                    "Volume": 1000,
                },
            )
        ]
    )


def test_data_receives_provider_truth_without_normalization() -> None:
    """Data receives the exact provider values mapped by the domain itself."""
    transport = _StubTransport(_provider_table())
    adapter = YahooBrokerAdapter(_config(), _capabilities(), transport=transport)

    async def exercise() -> None:
        result = await adapter.get_historical_bars(_SYMBOL, "1d", limit=1)
        assert result.is_success, result.error
        page = result.data
        assert page is not None

        # The page was produced by the domain's mapping, not handed to it.
        assert len(page.items) == 1
        bar = page.items[0]
        assert isinstance(bar, BrokerBar)

        # Provider truth is preserved exactly, with no normalization or rounding.
        assert bar.symbol == _SYMBOL
        assert bar.open == Decimal("150.25")
        assert bar.high == Decimal("152.50")
        assert bar.low == Decimal("149.75")
        assert bar.close == Decimal("151.00")

        # Timestamps are UTC-aware and never zero-duration (DEC-BRK-001 guard).
        assert bar.opening_timestamp == _OPENED_AT
        assert bar.closing_timestamp - bar.opening_timestamp == timedelta(days=1)
        assert bar.requested_timeframe == "1d"

        # The exact provider-native symbol crossed the boundary unchanged.
        assert transport.requested == [(_SYMBOL, "1d")]

    asyncio.run(exercise())


def test_empty_provider_page_is_never_fabricated_into_bars() -> None:
    """An empty successful provider response returns invalid, never synthetic."""
    adapter = YahooBrokerAdapter(
        _config(), _capabilities(), transport=_StubTransport(_Table([]))
    )

    async def exercise() -> None:
        result = await adapter.get_historical_bars(_SYMBOL, "1d", limit=1)
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_RESPONSE_INVALID

    asyncio.run(exercise())


def test_unsupported_observation_never_calls_provider() -> None:
    """A capability declared unavailable returns unsupported with zero calls."""
    capabilities = _capabilities()
    capabilities[BrokerCapabilityId.GET_ORDER_BOOK] = BrokerCapability(
        capability=BrokerCapabilityId.GET_ORDER_BOOK,
        implementation_status="NOT_IMPLEMENTED",
        availability="UNAVAILABLE",
        access_mode="READ",
        requirement="NONE",
        verification_status="NOT_TESTED",
        execution_model="PROVIDER_CALL",
    )
    transport = _StubTransport(_provider_table())
    adapter = YahooBrokerAdapter(_config(), capabilities, transport=transport)

    async def exercise() -> None:
        result = await adapter.get_order_book(_SYMBOL)
        assert not result.is_success
        assert result.error is not None
        assert result.error.code == BrokerErrorCode.BROKER_CAPABILITY_UNSUPPORTED

    asyncio.run(exercise())
    assert transport.requested == []
