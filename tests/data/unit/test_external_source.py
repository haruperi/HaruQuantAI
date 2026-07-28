"""Tests for the Brokers-backed Data source adapter."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers import (
    BrokerBar,
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
    BrokerPage,
    BrokerTick,
)
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.sources.broker_adapter import ExternalMarketDataSource
from app.services.data.sources.contracts import SourceReadRequest
from app.utils import StandardResponse, generate_id

from tests.brokers.response_factory import broker_response

_REQ_ID = "req-00000000-0000-4000-8000-000000000000"


def _unwrap(response):
    """Extract the raw payload from a StandardResponse for assertions."""
    return unwrap_data_response(
        response, operation="data.sources.test", request_id=_REQ_ID
    )


def test_bar_spread_evidence_crosses_the_broker_data_boundary() -> None:
    """Provider-reported per-bar spread remains exact and unit-bearing."""
    opening = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    closing = opening + timedelta(minutes=1)
    retrieved = closing + timedelta(days=1)

    class _Adapter:
        async def get_historical_bars(
            self,
            *,
            symbol: str,
            timeframe: str,
            start: datetime | None,
            end: datetime | None,
            limit: int,
        ) -> StandardResponse[BrokerPage[BrokerBar]]:
            del start, end
            bar = BrokerBar(
                symbol=symbol,
                opening_timestamp=opening,
                closing_timestamp=closing,
                is_closed=True,
                open=Decimal("1.1"),
                high=Decimal("1.2"),
                low=Decimal("1.0"),
                close=Decimal("1.15"),
                provider_timeframe=timeframe,
                requested_timeframe=timeframe,
                price_unit="quote_currency",
                quantity_unit="lots",
                tick_volume=Decimal(25),
                spread=Decimal(2),
                spread_unit="points",
            )
            return broker_response(
                BrokerCapabilityId.GET_HISTORICAL_BARS,
                broker=BrokerId.MT5,
                request_id=generate_id("req"),
                timestamp=retrieved,
                environment=BrokerEnvironment.DEMO,
                adapter_version="1.0.0",
                data=BrokerPage(items=(bar,), limit=limit, truncated=False),
            )

    batch = _unwrap(
        ExternalMarketDataSource("mt5", _Adapter()).fetch(
            SourceReadRequest(
                source_id="mt5",
                provider_symbol="EURUSD",
                data_kind="bars",
                timeframe="M1",
                limit=10,
                request_id=generate_id("req"),
            )
        )
    )

    assert batch.records[0]["spread"] == Decimal(2)
    assert batch.records[0]["spread_unit"] == "points"
    assert batch.records[0]["available_at"] == closing
    assert batch.retrieved_at == retrieved


def test_tick_availability_tolerates_provider_clock_skew() -> None:
    """Tick evidence remains valid when the provider clock leads local time."""
    received_at = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    event_at = received_at + timedelta(seconds=1)

    class _Adapter:
        async def get_ticks(
            self,
            *,
            symbol: str,
            start: datetime | None,
            end: datetime | None,
            limit: int,
        ) -> StandardResponse[BrokerPage[BrokerTick]]:
            del start, end
            tick = BrokerTick(
                symbol=symbol,
                event_timestamp=event_at,
                provider_receipt_timestamp=received_at,
                price_unit="quote_currency",
                quantity_unit="lots",
                bid=Decimal("1.1"),
                ask=Decimal("1.1002"),
            )
            return broker_response(
                BrokerCapabilityId.GET_TICKS,
                broker=BrokerId.MT5,
                request_id=generate_id("req"),
                timestamp=received_at,
                environment=BrokerEnvironment.DEMO,
                adapter_version="1.0.0",
                data=BrokerPage(items=(tick,), limit=limit, truncated=False),
            )

    request_id = generate_id("req")
    batch = _unwrap(
        ExternalMarketDataSource("mt5", _Adapter()).fetch(
            SourceReadRequest(
                source_id="mt5",
                provider_symbol="EURUSD",
                data_kind="ticks",
                limit=10,
                request_id=request_id,
            )
        )
    )

    assert batch.records[0]["available_at"] == event_at
    assert batch.retrieved_at == event_at
