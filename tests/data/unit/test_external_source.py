"""Tests for the Brokers-backed Data source adapter."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.brokers import (
    build_broker_value,
    get_broker_capability_id,
    get_broker_environment,
    get_broker_id,
)
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.sources.broker_adapter import ExternalMarketDataSource
from app.services.data.sources.contracts import SourceReadRequest
from app.utils import generate_id
from app.utils.responses.models import StandardResponse

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
        ) -> StandardResponse[object]:
            del start, end
            bar = build_broker_value(
                "bar",
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
                get_broker_capability_id("get_historical_bars"),
                broker=get_broker_id("mt5"),
                request_id=generate_id("req"),
                timestamp=retrieved,
                environment=get_broker_environment("demo"),
                adapter_version="1.0.0",
                data=build_broker_value(
                    "page", items=(bar,), limit=limit, truncated=False
                ),
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
        ) -> StandardResponse[object]:
            del start, end
            tick = build_broker_value(
                "tick",
                symbol=symbol,
                event_timestamp=event_at,
                provider_receipt_timestamp=received_at,
                price_unit="quote_currency",
                quantity_unit="lots",
                bid=Decimal("1.1"),
                ask=Decimal("1.1002"),
            )
            return broker_response(
                get_broker_capability_id("get_ticks"),
                broker=get_broker_id("mt5"),
                request_id=generate_id("req"),
                timestamp=received_at,
                environment=get_broker_environment("demo"),
                adapter_version="1.0.0",
                data=build_broker_value(
                    "page", items=(tick,), limit=limit, truncated=False
                ),
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
