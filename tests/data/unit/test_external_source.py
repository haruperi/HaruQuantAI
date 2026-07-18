"""Tests for the Brokers-backed Data source adapter."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers import (
    BrokerBar,
    BrokerCapabilityId,
    BrokerEnvironment,
    BrokerId,
    BrokerPage,
    BrokerResult,
    BrokerTick,
)
from app.services.data.contracts import SourceReadRequest
from app.services.data.sources.external import ExternalMarketDataSource
from app.utils import generate_id


def test_bar_spread_evidence_crosses_the_broker_data_boundary() -> None:
    """Provider-reported per-bar spread remains exact and unit-bearing."""
    opening = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    closing = opening + timedelta(minutes=1)

    class _Adapter:
        async def get_historical_bars(
            self,
            *,
            symbol: str,
            timeframe: str,
            start: datetime | None,
            end: datetime | None,
            limit: int,
        ) -> BrokerResult[BrokerPage[BrokerBar]]:
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
            return BrokerResult(
                status="success",
                broker=BrokerId.MT5,
                operation=BrokerCapabilityId.GET_HISTORICAL_BARS,
                request_id="get-bars-1",
                timestamp=closing,
                environment=BrokerEnvironment.DEMO,
                adapter_version="1.0.0",
                data=BrokerPage(items=(bar,), limit=limit, truncated=False),
            )

    batch = ExternalMarketDataSource("mt5", _Adapter()).fetch(
        SourceReadRequest(
            source_id="mt5",
            provider_symbol="EURUSD",
            data_kind="bars",
            timeframe="M1",
            limit=10,
            request_id=generate_id("req"),
        )
    )

    assert batch.records[0]["spread"] == Decimal(2)
    assert batch.records[0]["spread_unit"] == "points"


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
        ) -> BrokerResult[BrokerPage[BrokerTick]]:
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
            return BrokerResult(
                status="success",
                broker=BrokerId.MT5,
                operation=BrokerCapabilityId.GET_TICKS,
                request_id="get_ticks-1",
                timestamp=received_at,
                environment=BrokerEnvironment.DEMO,
                adapter_version="1.0.0",
                data=BrokerPage(items=(tick,), limit=limit, truncated=False),
            )

    request_id = generate_id("req")
    batch = ExternalMarketDataSource("mt5", _Adapter()).fetch(
        SourceReadRequest(
            source_id="mt5",
            provider_symbol="EURUSD",
            data_kind="ticks",
            limit=10,
            request_id=request_id,
        )
    )

    assert batch.records[0]["available_at"] == event_at
    assert batch.retrieved_at == event_at
