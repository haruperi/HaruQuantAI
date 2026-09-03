"""Unit tests for Real-Time Market Events service implementation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from app.contracts.catalogue.models import InstrumentRef, ProviderRef
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    MarketEvent,
    StreamMarketEventsRequest,
    StreamMarketEventsSubscription,
    StreamMarketEventsSuccess,
)
from app.services.data.realtime_market_events.config import (
    RealtimeMarketEventsConfig,
)
from app.services.data.realtime_market_events.realtime_market_events import (
    StreamMarketEventsService,
    _generate_uuid7,
    _run_usage_scenarios,
    compute_raw_hash,
)

if TYPE_CHECKING:
    from app.contracts.common.models import JsonObject


@pytest.mark.asyncio
async def test_bind_feed_success() -> None:
    """Test FR-DATA-TRACK_FEED_STATE: BIND_FEED creates feed state."""
    service = StreamMarketEventsService()
    provider_id = _generate_uuid7()
    req = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND_FEED",
        provider_id=provider_id,
    )
    res = await service.stream_market_events(req)
    assert isinstance(res, StreamMarketEventsSuccess)
    assert res.feed_state is not None
    assert res.feed_state.provider.provider_id == provider_id
    assert res.feed_state.generation == 1
    assert res.feed_state.state == "CONNECTING"
    assert res.outcome == "SUCCESS"


@pytest.mark.asyncio
async def test_bind_feed_idempotent() -> None:
    """Test that binding the same provider returns existing feed."""
    service = StreamMarketEventsService()
    provider_id = _generate_uuid7()
    req1 = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND_FEED",
        provider_id=provider_id,
    )
    res1 = await service.stream_market_events(req1)
    assert isinstance(res1, StreamMarketEventsSuccess)

    req2 = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND_FEED",
        provider_id=provider_id,
    )
    res2 = await service.stream_market_events(req2)
    assert isinstance(res2, StreamMarketEventsSuccess)
    assert res1.feed_state.feed_id == res2.feed_state.feed_id  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_feed_state_not_found() -> None:
    """Test FEED_STATE failure on unknown feed ID."""
    service = StreamMarketEventsService()
    req = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="FEED_STATE",
        feed_id=_generate_uuid7(),
    )
    res = await service.stream_market_events(req)
    assert isinstance(res, DataFailure)
    assert res.code == "DATA_NOT_FOUND"


@pytest.mark.asyncio
async def test_normalize_and_ingest_quote() -> None:
    """Test FR-DATA-NORMALIZE_LIVE_EVENTS: Quote event normalization."""
    service = StreamMarketEventsService()
    provider_id = _generate_uuid7()
    inst_id = _generate_uuid7()
    raw: JsonObject = {"bid": "1.09000", "ask": "1.09010"}

    event = MarketEvent(
        event_id=_generate_uuid7(),
        provider=ProviderRef(provider_id=provider_id, provider_name="TEST_FEED"),
        event_kind="QUOTE",
        event_time="2026-08-29T12:00:00.000000Z",
        receipt_time="2026-08-29T12:00:00.002000Z",
        provider_sequence=1,
        ordering_mode="PROVIDER_SEQUENCE",
        instrument=InstrumentRef(instrument_id=inst_id),
        values=raw,
        raw_hash=compute_raw_hash(raw),
    )
    await service.ingest_event(event)

    # Check feed was created and transitioned to LIVE
    req = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND_FEED",
        provider_id=provider_id,
    )
    res = await service.stream_market_events(req)
    assert isinstance(res, StreamMarketEventsSuccess)
    assert res.feed_state.state == "LIVE"  # type: ignore[union-attr]
    assert res.feed_state.last_event_at == event.receipt_time  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_order_live_events_gap_detection() -> None:
    """Test FR-DATA-ORDER_LIVE_EVENTS: Sequence gap transitions feed state to GAP."""
    service = StreamMarketEventsService()
    provider_id = _generate_uuid7()
    prov = ProviderRef(provider_id=provider_id, provider_name="TEST_FEED")

    # Ingest sequence 1
    ev1 = MarketEvent(
        event_id=_generate_uuid7(),
        provider=prov,
        event_kind="TICK",
        event_time="2026-08-29T12:00:00.000000Z",
        receipt_time="2026-08-29T12:00:00.001000Z",
        provider_sequence=1,
        ordering_mode="PROVIDER_SEQUENCE",
        values={"price": "1.08000"},
        raw_hash=compute_raw_hash({"price": "1.08000"}),
    )
    await service.ingest_event(ev1)

    # Ingest sequence 4 (gap: missed 2, 3)
    ev2 = MarketEvent(
        event_id=_generate_uuid7(),
        provider=prov,
        event_kind="TICK",
        event_time="2026-08-29T12:00:01.000000Z",
        receipt_time="2026-08-29T12:00:01.001000Z",
        provider_sequence=4,
        ordering_mode="PROVIDER_SEQUENCE",
        values={"price": "1.08005"},
        raw_hash=compute_raw_hash({"price": "1.08005"}),
    )
    await service.ingest_event(ev2)

    bind_res = await service.stream_market_events(
        StreamMarketEventsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="BIND_FEED",
            provider_id=provider_id,
        )
    )
    assert isinstance(bind_res, StreamMarketEventsSuccess)
    assert bind_res.feed_state.state == "GAP"  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_reconnect_lifecycle_uncovered_intervals() -> None:
    """Test FR-DATA-RECONNECT_MARKET_FEEDS: Disconnect, generation bump, and uncovered intervals."""
    service = StreamMarketEventsService()
    provider_id = _generate_uuid7()
    bind_res = await service.stream_market_events(
        StreamMarketEventsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="BIND_FEED",
            provider_id=provider_id,
        )
    )
    assert isinstance(bind_res, StreamMarketEventsSuccess)
    feed_id = bind_res.feed_state.feed_id  # type: ignore[union-attr]

    # Disconnect
    disc_state = await service.simulate_disconnect(
        feed_id, "2026-08-29T12:05:00.000000Z"
    )
    assert disc_state.state == "RECONNECTING"

    # Reconnect
    recon_state = await service.reconnect_feed(feed_id, "2026-08-29T12:05:30.000000Z")
    assert recon_state.state == "LIVE"
    assert recon_state.generation == 2
    assert len(recon_state.uncovered_intervals) == 1
    assert recon_state.uncovered_intervals[0].from_at == "2026-08-29T12:05:00.000000Z"
    assert recon_state.uncovered_intervals[0].to_at == "2026-08-29T12:05:30.000000Z"


@pytest.mark.asyncio
async def test_record_market_replays() -> None:
    """Test FR-DATA-RECORD_MARKET_REPLAYS: Generating bounded replay reference."""
    service = StreamMarketEventsService()
    provider_id = _generate_uuid7()
    prov = ProviderRef(provider_id=provider_id, provider_name="TEST_FEED")
    inst = InstrumentRef(instrument_id=_generate_uuid7())

    # Ingest 3 events
    for seq, t in enumerate(["12:00:01", "12:00:02", "12:00:03"], start=1):
        ts = f"2026-08-29T{t}.000000Z"
        ev = MarketEvent(
            event_id=_generate_uuid7(),
            provider=prov,
            event_kind="TICK",
            event_time=ts,
            receipt_time=ts,
            provider_sequence=seq,
            ordering_mode="PROVIDER_SEQUENCE",
            instrument=inst,
            values={"tick_index": seq},
            raw_hash=compute_raw_hash({"tick_index": seq}),
        )
        await service.ingest_event(ev)

    bind_res = await service.stream_market_events(
        StreamMarketEventsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="BIND_FEED",
            provider_id=provider_id,
        )
    )
    assert isinstance(bind_res, StreamMarketEventsSuccess)
    feed_id = bind_res.feed_state.feed_id  # type: ignore[union-attr]

    replay_req = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="REPLAY",
        feed_id=feed_id,
        from_at="2026-08-29T12:00:00.000000Z",
        to_at="2026-08-29T12:00:02.500000Z",
    )
    replay_res = await service.stream_market_events(replay_req)
    assert isinstance(replay_res, StreamMarketEventsSuccess)
    assert replay_res.replay is not None
    assert replay_res.replay.event_count == 2
    assert replay_res.replay.from_at == "2026-08-29T12:00:00.000000Z"
    assert replay_res.replay.to_at == "2026-08-29T12:00:02.500000Z"
    assert len(replay_res.replay.partition_artifact_ids) == 1


@pytest.mark.asyncio
async def test_subscription_live_stream_and_replay_limit() -> None:
    """Test FR-DATA-BOUND_EVENT_BUFFERS: Live event subscription and replay buffer bounds."""
    service = StreamMarketEventsService(
        config=RealtimeMarketEventsConfig(buffer_capacity=100)
    )
    provider_id = _generate_uuid7()
    prov = ProviderRef(provider_id=provider_id, provider_name="TEST_FEED")
    inst = InstrumentRef(instrument_id=_generate_uuid7())

    # Ingest 3 initial events
    for seq in range(1, 4):
        ts = f"2026-08-29T12:00:0{seq}.000000Z"
        await service.ingest_event(
            MarketEvent(
                event_id=_generate_uuid7(),
                provider=prov,
                event_kind="TICK",
                event_time=ts,
                receipt_time=ts,
                provider_sequence=seq,
                ordering_mode="PROVIDER_SEQUENCE",
                instrument=inst,
                values={"seq": seq},
                raw_hash=compute_raw_hash({"seq": seq}),
            )
        )

    # Subscribe with replay_limit = 2
    sub_req = StreamMarketEventsSubscription(
        provider_id=provider_id,
        instruments=(inst,),
        replay_limit=2,
    )

    received = []

    async def _consume() -> None:
        async for dom_ev in service.subscribe_stream_market_events_events(sub_req):
            received.append(dom_ev)
            if len(received) >= 3:
                break

    task = asyncio.create_task(_consume())
    await asyncio.sleep(0.05)

    # Ingest a 4th event live
    ts4 = "2026-08-29T12:00:04.000000Z"
    await service.ingest_event(
        MarketEvent(
            event_id=_generate_uuid7(),
            provider=prov,
            event_kind="TICK",
            event_time=ts4,
            receipt_time=ts4,
            provider_sequence=4,
            ordering_mode="PROVIDER_SEQUENCE",
            instrument=inst,
            values={"seq": 4},
            raw_hash=compute_raw_hash({"seq": 4}),
        )
    )

    await asyncio.wait_for(task, timeout=2.0)
    assert len(received) == 3
    # First two were replayed (seq 2, 3), third was live (seq 4)
    replayed_second = received[0].payload["values"]
    replayed_third = received[1].payload["values"]
    live_fourth = received[2].payload["values"]
    assert isinstance(replayed_second, dict)
    assert isinstance(replayed_third, dict)
    assert isinstance(live_fourth, dict)
    assert replayed_second["seq"] == 2
    assert replayed_third["seq"] == 3
    assert live_fourth["seq"] == 4


@pytest.mark.asyncio
async def test_stream_market_events_validation_failures() -> None:
    """Verify DataFailure on missing provider, missing feed, and invalid replay range."""
    service = StreamMarketEventsService()

    # BIND_FEED missing provider_id
    req_no_prov = StreamMarketEventsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND_FEED",
        provider_id=None,
        schema_version=1,
    )
    res1 = await service.stream_market_events(req_no_prov)
    assert isinstance(res1, DataFailure)
    assert res1.code == "DATA_VALIDATION_FAILED"

    # FEED_STATE unknown feed
    req_unknown_feed = StreamMarketEventsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="FEED_STATE",
        feed_id="nonexistent-feed",
        schema_version=1,
    )
    res2 = await service.stream_market_events(req_unknown_feed)
    assert isinstance(res2, DataFailure)
    assert res2.code == "DATA_NOT_FOUND"

    # REPLAY unknown feed
    req_unknown_replay = StreamMarketEventsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="REPLAY",
        feed_id="nonexistent-feed",
        from_at="2026-08-29T12:00:00.000000Z",
        to_at="2026-08-29T12:05:00.000000Z",
        schema_version=1,
    )
    res3 = await service.stream_market_events(req_unknown_replay)
    assert isinstance(res3, DataFailure)
    assert res3.code == "DATA_NOT_FOUND"


@pytest.mark.asyncio
async def test_disconnect_and_reconnect_unknown_feed() -> None:
    """Verify KeyError when simulating disconnect or reconnect on unknown feed."""
    service = StreamMarketEventsService()
    with pytest.raises(KeyError, match="Feed 'unknown' not found"):
        await service.simulate_disconnect("unknown")
    with pytest.raises(KeyError, match="Feed 'unknown' not found"):
        await service.reconnect_feed("unknown")


@pytest.mark.asyncio
async def test_run_usage_scenarios_harness() -> None:
    """Verify execution of standalone usage scenarios."""
    await _run_usage_scenarios()


def test_realtime_event_persistence() -> None:
    """Verify RealtimeEventPersistence operations and state transitions."""
    from app.services.data.realtime_market_events._persistence import (
        RealtimeEventPersistence,
    )
    from app.services.data.realtime_market_events.config import (
        RealtimeMarketEventsConfig,
    )

    p = RealtimeEventPersistence(RealtimeMarketEventsConfig())
    p.bind_provider("p1", "f1")
    assert p.get_feed_id_for_provider("p1") == "f1"
    assert p.get_feed_id_for_provider("unknown") is None

    p.set_last_sequence("f1", 42)
    assert p.get_last_sequence("f1") == 42
    assert p.get_last_sequence("unknown") is None

    p.record_disconnect("f1", "2026-08-29T12:00:00.000000Z")
    assert p.pop_disconnect("f1") == "2026-08-29T12:00:00.000000Z"
    assert p.pop_disconnect("f1") is None

    p.clear()
    assert p.get_feed_id_for_provider("p1") is None
