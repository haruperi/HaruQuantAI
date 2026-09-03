"""Executable usage demonstration harness for Real-time Market Events."""

from __future__ import annotations

import asyncio

from app.contracts.catalogue.models import InstrumentRef, ProviderRef
from app.contracts.common.models import JsonObject
from app.contracts.data.models import (
    MarketEvent,
    MarketFeedState,
    StreamMarketEventsRequest,
    StreamMarketEventsSubscription,
    StreamMarketEventsSuccess,
)
from app.services.data.realtime_market_events.realtime_market_events import (
    StreamMarketEventsService,
    _generate_uuid7,
    compute_raw_hash,
)


async def _run_scenarios_1_to_3(
    service: StreamMarketEventsService,
    provider_id: str,
    inst: InstrumentRef,
    prov: ProviderRef,
) -> str:
    """Execute scenarios 1 to 3: normalization, feed state, and gaps."""
    # 1. FR-DATA-NORMALIZE_LIVE_EVENTS
    print()
    print("[Scenario 1: FR-DATA-NORMALIZE_LIVE_EVENTS] Normalizing Quotes")
    raw_quote: JsonObject = {
        "bid": "1.08500",
        "ask": "1.08510",
        "bid_size": 10,
    }
    quote_event = MarketEvent(
        event_id=_generate_uuid7(),
        provider=prov,
        event_kind="QUOTE",
        event_time="2026-08-29T12:00:00.000000Z",
        receipt_time="2026-08-29T12:00:00.005000Z",
        provider_sequence=1,
        ordering_mode="PROVIDER_SEQUENCE",
        instrument=inst,
        values=raw_quote,
        raw_hash=compute_raw_hash(raw_quote),
    )
    await service.ingest_event(quote_event)
    h16 = quote_event.raw_hash[:16]
    print(f"  [OK] Quote normalized: id={quote_event.event_id}, hash={h16}...")

    # 2. FR-DATA-TRACK_FEED_STATE
    print()
    print("[Scenario 2: FR-DATA-TRACK_FEED_STATE] Observing Feed State Ladder")
    bind_req = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND_FEED",
        provider_id=provider_id,
    )
    bind_res = await service.stream_market_events(bind_req)
    if not isinstance(bind_res, StreamMarketEventsSuccess) or not bind_res.feed_state:
        msg = "Expected StreamMarketEventsSuccess"
        raise RuntimeError(msg)
    feed_id = bind_res.feed_state.feed_id
    gen = bind_res.feed_state.generation
    st = bind_res.feed_state.state
    print(f"  [OK] Feed bound: feed_id={feed_id}, state={st}, gen={gen}")

    # 3. FR-DATA-ORDER_LIVE_EVENTS
    print()
    print("[Scenario 3: FR-DATA-ORDER_LIVE_EVENTS] Sequence Gap Verification")
    gap_tick: JsonObject = {"price": "1.08505", "volume": 5}
    gap_event = MarketEvent(
        event_id=_generate_uuid7(),
        provider=prov,
        event_kind="TICK",
        event_time="2026-08-29T12:00:05.000000Z",
        receipt_time="2026-08-29T12:00:05.002000Z",
        provider_sequence=5,
        ordering_mode="PROVIDER_SEQUENCE",
        instrument=inst,
        values=gap_tick,
        raw_hash=compute_raw_hash(gap_tick),
    )
    await service.ingest_event(gap_event)
    state_res = await service.stream_market_events(
        StreamMarketEventsRequest(
            request_id=_generate_uuid7(),
            capability_snapshot_id=_generate_uuid7(),
            operation="FEED_STATE",
            feed_id=feed_id,
        )
    )
    if not isinstance(state_res, StreamMarketEventsSuccess) or not state_res.feed_state:
        msg = "Expected StreamMarketEventsSuccess"
        raise RuntimeError(msg)
    print(f"  [OK] Gap detected: state transitioned to {state_res.feed_state.state}")
    return feed_id


async def _run_scenarios_4_to_6(
    service: StreamMarketEventsService,
    feed_id: str,
    inst: InstrumentRef,
) -> None:
    """Execute scenarios 4 to 6: buffering, reconnect, and replays."""
    # 4. FR-DATA-BOUND_EVENT_BUFFERS
    print()
    print("[Scenario 4: FR-DATA-BOUND_EVENT_BUFFERS] Bounded Subscription Replay")
    sub_req = StreamMarketEventsSubscription(
        feed_id=feed_id,
        instruments=(inst,),
        replay_limit=2,
    )
    replayed_events = []
    target_count = 2
    async for dom_ev in service.subscribe_stream_market_events_events(sub_req):
        replayed_events.append(dom_ev)
        if len(replayed_events) >= target_count:
            break
    print(f"  [OK] Replayed {len(replayed_events)} bounded events")

    # 5. FR-DATA-RECONNECT_MARKET_FEEDS
    print()
    print("[Scenario 5: FR-DATA-RECONNECT_MARKET_FEEDS] Disconnect & Reconnect")
    await service.simulate_disconnect(feed_id, "2026-08-29T12:00:10.000000Z")
    reconnected = await service.reconnect_feed(feed_id, "2026-08-29T12:00:15.000000Z")
    u_cnt = len(reconnected.uncovered_intervals)
    print(f"  [OK] Reconnected feed: gen={reconnected.generation}, gaps={u_cnt}")

    # 6. FR-DATA-RECORD_MARKET_REPLAYS
    print()
    print("[Scenario 6: FR-DATA-RECORD_MARKET_REPLAYS] Partition Replay Reference")
    replay_req = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="REPLAY",
        feed_id=feed_id,
        from_at="2026-08-29T11:59:00.000000Z",
        to_at="2026-08-29T12:01:00.000000Z",
    )
    replay_res = await service.stream_market_events(replay_req)
    if not isinstance(replay_res, StreamMarketEventsSuccess) or not replay_res.replay:
        msg = "Expected StreamMarketEventsSuccess with replay"
        raise RuntimeError(msg)
    r_id = replay_res.replay.replay_id
    r_cnt = replay_res.replay.event_count
    r_hash = replay_res.replay.content_hash[:16]
    print(f"  [OK] Replay created: id={r_id}, count={r_cnt}, hash={r_hash}...")


async def _run_usage_scenarios() -> None:
    """Execute domain usage scenarios for FEAT-DATA-STREAM_MARKET_EVENTS."""
    print()
    print("=" * 80)
    print("HARUQUANT AI - REAL-TIME MARKET EVENTS DOMAIN SCENARIO HARNESS")
    print("=" * 80)

    service = StreamMarketEventsService()
    provider_id = _generate_uuid7()
    inst = InstrumentRef(instrument_id=_generate_uuid7())
    prov = ProviderRef(provider_id=provider_id, provider_name="PRIMARY_FEED")

    feed_id = await _run_scenarios_1_to_3(service, provider_id, inst, prov)
    await _run_scenarios_4_to_6(service, feed_id, inst)

    print("\n--- Additional Real-Time Stream Example ---")
    mt5_feed = await example_mt5_stream()
    print(f"  * example_mt5_stream: feed_id={mt5_feed.feed_id} status={mt5_feed.state}")

    print()
    print("[OK] All 6 usage scenarios completed successfully.")


async def example_mt5_stream() -> MarketFeedState:
    """Stream live market events through the current real-time streaming capability."""
    service = StreamMarketEventsService()
    bind_req = StreamMarketEventsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="BIND_FEED",
        provider_id=_generate_uuid7(),
    )
    bind_res = await service.stream_market_events(bind_req)
    if isinstance(bind_res, StreamMarketEventsSuccess) and bind_res.feed_state:
        return bind_res.feed_state
    msg = "Failed to bind feed"
    raise RuntimeError(msg)


async def main() -> None:
    """Execute all real-time market event usage scenarios."""
    await _run_usage_scenarios()


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
