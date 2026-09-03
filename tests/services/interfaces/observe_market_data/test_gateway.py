"""Gateway behavior tests for observe-market-data."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid7

import pytest
from app.contracts.interfaces.errors import InterfaceFailure
from app.contracts.interfaces.models import (
    ObserveMarketDataEventSubscription,
    ObserveMarketDataRequest,
    ObserveMarketDataSuccess,
)
from app.services.interfaces.observe_market_data.config import ObserveMarketDataConfig
from app.services.interfaces.observe_market_data.gateway import MarketDataGateway

from tests.services.interfaces.observe_market_data.fakes import (
    FailingStreamProvider,
    FakeStreamProvider,
    QueuedStreamProvider,
    format_timestamp,
    make_event,
)

_EVENT_TIME = datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)


class _FixedClock:
    """Deterministic UTC clock for staleness tests."""

    def __init__(self, moment: datetime) -> None:
        """Initialize the controlled instant."""
        self.now = moment

    def __call__(self) -> datetime:
        """Return the controlled instant."""
        return self.now


def _request(symbols: tuple[str, ...] = ()) -> ObserveMarketDataRequest:
    """Build a SNAPSHOT request."""
    return ObserveMarketDataRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="SNAPSHOT",
        symbols=symbols,
    )


def _snapshot(result: object) -> ObserveMarketDataSuccess:
    """Narrow a successful gateway result."""
    assert isinstance(result, ObserveMarketDataSuccess)
    assert result.snapshot is not None
    return result


async def _drain(gateway: MarketDataGateway) -> None:
    """Run the consumer until the scripted provider ends."""
    await gateway.run()


async def _live_gateway(
    events: tuple[object, ...],
    clock: _FixedClock,
    config: ObserveMarketDataConfig | None = None,
) -> tuple[MarketDataGateway, QueuedStreamProvider, asyncio.Task[None]]:
    """Build a gateway with a live queued provider and consumer task."""
    provider = QueuedStreamProvider()
    gateway = MarketDataGateway(
        provider,
        config or ObserveMarketDataConfig(),
        clock=clock,
    )
    consumer = asyncio.create_task(gateway.run())
    for _ in range(20):
        await asyncio.sleep(0)
    for event in events:
        provider.publish(event)  # type: ignore[arg-type]
    for _ in range(20):
        await asyncio.sleep(0)
    return gateway, provider, consumer


@pytest.mark.asyncio
async def test_snapshot_projection_sequence_source_and_quotes() -> None:
    """Verify projection, sequence, gap counting, and source identity."""
    clock = _FixedClock(_EVENT_TIME)
    gateway, _provider, consumer = await _live_gateway(
        (
            make_event(1, "EURUSD", "1.085", "1.0852", occurred_at=_EVENT_TIME),
            make_event(2, "GBPUSD", "1.2693", "1.2695", occurred_at=_EVENT_TIME),
            make_event(4, "EURUSD", "1.0851", "1.0853", occurred_at=_EVENT_TIME),
        ),
        clock,
    )

    snapshot = _snapshot(await gateway.observe_market_data(_request())).snapshot
    assert snapshot is not None
    assert snapshot.sequence == 4
    assert snapshot.gap == 1
    assert snapshot.source_id == "data.stream-market-events@1"
    assert snapshot.occurred_at == format_timestamp(_EVENT_TIME)
    assert snapshot.stale is False
    assert snapshot.stale_reason is None
    assert [quote.symbol for quote in snapshot.quotes] == ["EURUSD", "GBPUSD"]
    eurusd = snapshot.quotes[0]
    assert eurusd.bid == "1.0851"
    assert eurusd.ask == "1.0853"

    gateway.close()
    _provider.finish()
    await asyncio.wait_for(consumer, timeout=1.0)


@pytest.mark.asyncio
async def test_snapshot_stale_before_first_event() -> None:
    """Verify honest staleness with no received events."""
    gateway = MarketDataGateway(
        FakeStreamProvider(),
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    snapshot = _snapshot(await gateway.observe_market_data(_request())).snapshot
    assert snapshot is not None
    assert snapshot.sequence == 0
    assert snapshot.quotes == ()
    assert snapshot.stale is True
    assert snapshot.stale_reason == "no market events received yet"


@pytest.mark.asyncio
async def test_snapshot_stale_by_event_age() -> None:
    """Verify age-based staleness against the configured threshold."""
    clock = _FixedClock(_EVENT_TIME)
    gateway, _provider, consumer = await _live_gateway(
        (make_event(1, occurred_at=_EVENT_TIME),),
        clock,
        ObserveMarketDataConfig(stale_after_seconds=5.0),
    )
    clock.now = _EVENT_TIME.replace(second=10)

    snapshot = _snapshot(await gateway.observe_market_data(_request())).snapshot
    assert snapshot is not None
    assert snapshot.stale is True
    assert snapshot.stale_reason is not None
    assert "stale_after_seconds" in snapshot.stale_reason

    gateway.close()
    _provider.finish()
    await asyncio.wait_for(consumer, timeout=1.0)


@pytest.mark.asyncio
async def test_symbol_filter_and_oversized_filter() -> None:
    """Verify bounded symbol filtering and rejection."""
    provider = FakeStreamProvider(
        (
            make_event(1, "EURUSD", occurred_at=_EVENT_TIME),
            make_event(2, "GBPUSD", occurred_at=_EVENT_TIME),
        )
    )
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(max_symbols=2),
        clock=_FixedClock(_EVENT_TIME),
    )
    await _drain(gateway)

    filtered = _snapshot(
        await gateway.observe_market_data(_request(("GBPUSD",)))
    ).snapshot
    assert filtered is not None
    assert [quote.symbol for quote in filtered.quotes] == ["GBPUSD"]

    oversized = await gateway.observe_market_data(_request(("A", "B", "C")))
    assert isinstance(oversized, InterfaceFailure)
    assert oversized.code == "INTERFACE_VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_provider_loss_degrades_but_keeps_last_truth() -> None:
    """Verify degraded staleness retains the last known quotes."""
    provider = FakeStreamProvider((make_event(1, "EURUSD", occurred_at=_EVENT_TIME),))
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    await _drain(gateway)
    assert gateway.degraded_reason == "market event provider stream ended"

    snapshot = _snapshot(await gateway.observe_market_data(_request())).snapshot
    assert snapshot is not None
    assert snapshot.stale is True
    assert snapshot.stale_reason == "market event provider stream ended"
    assert [quote.symbol for quote in snapshot.quotes] == ["EURUSD"]


@pytest.mark.asyncio
async def test_provider_failure_records_and_reraises() -> None:
    """Verify provider failures are recorded and re-raised."""
    provider = FailingStreamProvider((make_event(1, occurred_at=_EVENT_TIME),))
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    with pytest.raises(RuntimeError, match="provider exploded"):
        await gateway.run()
    assert gateway.degraded_reason == "market event provider stream failed"


@pytest.mark.asyncio
async def test_closed_gateway_fails_closed() -> None:
    """Verify disposal fails subsequent observation closed."""
    gateway = MarketDataGateway(
        FakeStreamProvider(),
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    gateway.close()
    gateway.close()

    result = await gateway.observe_market_data(_request())
    assert isinstance(result, InterfaceFailure)
    assert result.code == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_subscription_filters_symbols_and_passes_resume() -> None:
    """Verify filtered delivery with resume and replay passthrough."""
    provider = FakeStreamProvider(
        (
            make_event(1, "EURUSD", occurred_at=_EVENT_TIME),
            make_event(2, "GBPUSD", occurred_at=_EVENT_TIME),
            make_event(3, "EURUSD", occurred_at=_EVENT_TIME),
        )
    )
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    subscription = ObserveMarketDataEventSubscription(
        symbols=("EURUSD",),
        resume_event_id=None,
        replay_limit=5,
    )

    received = [
        event
        async for event in gateway.subscribe_observe_market_data_events(subscription)
    ]
    assert [event.sequence for event in received] == [1, 3]
    assert provider.subscriptions[-1].replay_limit == 5


@pytest.mark.asyncio
async def test_subscription_stops_on_gateway_close_and_disconnect() -> None:
    """Verify disposal and client disconnect release the subscription."""
    provider = QueuedStreamProvider()
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    stream = gateway.subscribe_observe_market_data_events(
        ObserveMarketDataEventSubscription()
    )
    pending_first = asyncio.ensure_future(anext(stream))
    for _ in range(10):
        await asyncio.sleep(0)
    provider.publish(make_event(1, occurred_at=_EVENT_TIME))
    first = await pending_first
    assert first.sequence == 1

    await stream.aclose()
    gateway.close()

    closed_stream = gateway.subscribe_observe_market_data_events(
        ObserveMarketDataEventSubscription()
    )
    pending_closed = asyncio.ensure_future(anext(closed_stream))
    for _ in range(10):
        await asyncio.sleep(0)
    provider.publish(make_event(2, occurred_at=_EVENT_TIME))
    with pytest.raises(StopAsyncIteration):
        await pending_closed


@pytest.mark.asyncio
async def test_malformed_payloads_advance_sequence_without_quotes() -> None:
    """Verify non-projectable payloads never invent quotes."""
    provider = FakeStreamProvider(
        (
            make_event(1, payload={"detail": "status"}),
            make_event(2, payload={"symbol": "EURUSD", "bid": "x", "ask": "1.1"}),
        )
    )
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    await _drain(gateway)

    snapshot = _snapshot(await gateway.observe_market_data(_request())).snapshot
    assert snapshot is not None
    assert snapshot.sequence == 2
    assert snapshot.quotes == ()


@pytest.mark.asyncio
async def test_run_returns_when_closed_mid_stream() -> None:
    """Verify the consumer stops after disposal."""
    provider = QueuedStreamProvider()
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(),
        clock=_FixedClock(_EVENT_TIME),
    )
    consumer = asyncio.create_task(gateway.run())
    for _ in range(10):
        await asyncio.sleep(0)
    provider.publish(make_event(1, occurred_at=_EVENT_TIME))
    await asyncio.sleep(0)
    gateway.close()
    provider.publish(make_event(2, occurred_at=_EVENT_TIME))
    await asyncio.sleep(0)
    await asyncio.wait_for(consumer, timeout=1.0)
    assert gateway.degraded_reason is None
