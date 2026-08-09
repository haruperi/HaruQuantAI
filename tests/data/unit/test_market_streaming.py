"""Behavioral coverage for Data-owned MT5 market streaming."""

from __future__ import annotations

import asyncio
from collections import Counter
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.data import (
    build_auction_payload,
    build_corporate_action_payload,
    build_depth_update_payload,
    build_halt_payload,
    build_market_stream_request,
    build_trade_payload,
    build_venue_state_payload,
)
from app.services.data.contracts import DataError, TickRecord
from app.services.data.realtime_feeds import mt5_bars, mt5_ticks, subscriptions
from app.services.data.realtime_feeds.contracts import (
    MarketStreamEvent,
    MarketStreamRequest,
)
from app.services.data.realtime_feeds.mt5_bars import _BarLike, _seconds_until_boundary
from app.services.data.realtime_feeds.mt5_ticks import (
    _signature,
    _TickLike,
    _unseen_ticks,
)
from app.services.data.realtime_feeds.subscriptions import (
    _HUBS,
    _admit_hub,
    _StreamHub,
    stream_market_data,
)
from app.utils import generate_id

_NOW = datetime(2026, 8, 3, 12, tzinfo=UTC)


def _tick(timestamp: datetime, bid: str) -> _TickLike:
    """Return one structural Brokers-tick fixture."""
    return cast(
        "_TickLike",
        SimpleNamespace(
            symbol="EURUSD",
            event_timestamp=timestamp,
            provider_receipt_timestamp=timestamp,
            price_unit="quote_currency",
            bid=Decimal(bid),
            ask=Decimal(bid) + Decimal("0.0001"),
            last_price=None,
            bid_quantity=None,
            ask_quantity=None,
        ),
    )


def _record(second: int) -> TickRecord:
    """Return one genuine-evidence canonical tick fixture."""
    timestamp = _NOW + timedelta(seconds=second)
    return TickRecord(
        timestamp=timestamp,
        source="mt5",
        source_symbol="EURUSD",
        source_revision="mt5-live-v1",
        available_at=timestamp,
        bid=Decimal("1.1000") + Decimal(second) / Decimal(10_000),
        ask=Decimal("1.1001") + Decimal(second) / Decimal(10_000),
        price_unit="quote_currency",
    )


def _bar(opening: datetime, close: str) -> _BarLike:
    """Return one structural closed Brokers-bar fixture."""
    return cast(
        "_BarLike",
        SimpleNamespace(
            symbol="EURUSD",
            opening_timestamp=opening,
            closing_timestamp=opening + timedelta(minutes=1),
            open=Decimal("1.1000"),
            high=Decimal("1.1010"),
            low=Decimal("1.0990"),
            close=Decimal(close),
            price_unit="quote_currency",
            quantity_unit="lots",
            trade_volume=Decimal(10),
            tick_volume=Decimal(25),
            spread=Decimal("0.0001"),
            spread_unit="quote_currency",
        ),
    )


class _Session:
    """Execute fake Brokers coroutines with the production thread boundary."""

    def adapter(self, _request_id: str) -> object:
        """Return one inert adapter identity."""
        return object()

    def run(self, operation: Any, _request_id: str) -> object:
        """Complete one fake broker operation in the worker thread."""
        return asyncio.run(operation)


def test_stream_request_validates_mode_source_and_timeframe() -> None:
    """Both stream modes accept canonical timeframes and reject unknown ones."""
    for mode in ("bars", "ticks"):
        request = build_market_stream_request(
            source_id="mt5",
            symbol="EURUSD",
            mode=mode,
            timeframe="M5",
            request_id=generate_id("req"),
        )
        assert request.mode == mode
        assert request.timeframe == "M5"

    with pytest.raises(DataError, match="UNSUPPORTED_TIMEFRAME"):
        build_market_stream_request(
            source_id="mt5",
            symbol="EURUSD",
            mode="ticks",
            timeframe="UNKNOWN",
            request_id=generate_id("req"),
        )


@pytest.mark.parametrize(
    ("now", "timeframe", "expected"),
    [
        (datetime(2026, 8, 3, 12, 0, 30, tzinfo=UTC), "M1", 30.0),
        (datetime(2026, 8, 3, 12, 3, tzinfo=UTC), "M5", 120.0),
        (datetime(2026, 8, 3, 12, 15, tzinfo=UTC), "H1", 2700.0),
    ],
)
def test_bar_mode_waits_for_exact_utc_timeframe_boundary(
    now: datetime,
    timeframe: str,
    expected: float,
) -> None:
    """M1, M5, and H1 polling aligns with their next close boundary."""
    assert _seconds_until_boundary(now, timeframe) == expected


def test_tick_overlap_deduplication_preserves_real_multiplicity() -> None:
    """Overlap is removed without collapsing distinct identical MT5 ticks."""
    first = _tick(_NOW, "1.1000")
    duplicate_value = _tick(_NOW, "1.1000")
    next_tick = _tick(_NOW + timedelta(milliseconds=1), "1.1001")
    prior = Counter({_signature(first): 1})

    unseen, cursor, counts = _unseen_ticks(
        (first, duplicate_value, next_tick),
        _NOW,
        prior,
    )

    assert unseen == (duplicate_value, next_tick)
    assert cursor == next_tick.event_timestamp
    assert counts[_signature(next_tick)] == 1


def test_mt5_tick_producer_reads_current_then_every_new_tick(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tick mode maps current and overlapping MT5 pages without duplication."""

    async def scenario() -> None:
        first = _tick(_NOW, "1.1000")
        second = _tick(_NOW + timedelta(milliseconds=1), "1.1001")
        pages = [
            SimpleNamespace(error=None, data=SimpleNamespace(items=(first,))),
            SimpleNamespace(error=None, data=SimpleNamespace(items=(first, second))),
        ]

        def read_ticks(*_args: object, **_kwargs: object) -> object:
            async def result() -> object:
                return pages.pop(0)

            return result()

        monkeypatch.setattr(
            mt5_ticks, "_resolve_realtime_session_raw", lambda *_: _Session()
        )
        monkeypatch.setattr(mt5_ticks, "get_broker_ticks", read_ticks)
        stream = mt5_ticks.iter_mt5_ticks(
            symbol="EURUSD",
            request_id=generate_id("req"),
        )
        current = await asyncio.wait_for(anext(stream), timeout=1)
        following = await asyncio.wait_for(anext(stream), timeout=1)
        await stream.aclose()

        assert current.bid == Decimal("1.1000")
        assert following.bid == Decimal("1.1001")
        assert not pages

    asyncio.run(scenario())


def test_mt5_bar_producer_emits_only_newly_closed_bars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bar mode maps the latest closed bar and the next timeframe close."""

    async def scenario() -> None:
        first = _bar(_NOW - timedelta(minutes=1), "1.1005")
        second = _bar(_NOW, "1.1007")
        pages = [
            SimpleNamespace(error=None, data=SimpleNamespace(items=(first,))),
            SimpleNamespace(error=None, data=SimpleNamespace(items=(second,))),
        ]

        def read_bars(*_args: object, **_kwargs: object) -> object:
            async def result() -> object:
                return pages.pop(0)

            return result()

        async def no_wait(_seconds: float) -> None:
            return None

        monkeypatch.setattr(
            mt5_bars, "_resolve_realtime_session_raw", lambda *_: _Session()
        )
        monkeypatch.setattr(mt5_bars, "get_broker_historical_bars", read_bars)
        monkeypatch.setattr(mt5_bars.asyncio, "sleep", no_wait)
        stream = mt5_bars.iter_mt5_closed_bars(
            symbol="EURUSD",
            timeframe="M1",
            request_id=generate_id("req"),
        )
        current = await asyncio.wait_for(anext(stream), timeout=1)
        following = await asyncio.wait_for(anext(stream), timeout=1)
        await stream.aclose()

        assert current.close == Decimal("1.1005")
        assert following.close == Decimal("1.1007")
        assert following.available_at == second.closing_timestamp
        assert not pages

    asyncio.run(scenario())


def test_shared_hub_fans_out_once_and_replays_retained_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent consumers share one producer and resume by sequence."""

    async def scenario() -> None:
        release = asyncio.Event()
        starts = 0

        async def producer() -> AsyncGenerator[TickRecord]:
            nonlocal starts
            starts += 1
            yield _record(1)
            yield _record(2)
            await release.wait()

        monkeypatch.setattr(_StreamHub, "_producer", lambda _self: producer())
        request = MarketStreamRequest(
            source_id="mt5",
            symbol="EURUSD",
            mode="ticks",
            timeframe="M1",
            request_id=generate_id("req"),
        )
        hub = _StreamHub(request)
        first = await hub.subscribe("first", None)
        first_event = await asyncio.wait_for(first.get(), timeout=1)
        second_event = await asyncio.wait_for(first.get(), timeout=1)
        assert first_event is not None
        assert second_event is not None

        resumed = await hub.subscribe("resumed", first_event.sequence)
        replay = await asyncio.wait_for(resumed.get(), timeout=1)
        assert replay == second_event
        assert starts == 1

        await hub.unsubscribe("resumed")
        await hub.unsubscribe("first")
        release.set()

    asyncio.run(scenario())


def test_hub_emits_one_terminal_gap_for_a_slow_consumer() -> None:
    """Backpressure is explicit and later events cannot replace the terminal gap."""

    async def scenario() -> None:
        request = MarketStreamRequest(
            source_id="mt5",
            symbol="EURUSD",
            mode="ticks",
            timeframe="M1",
            request_id=generate_id("req"),
        )
        hub = _StreamHub(request)
        queue = asyncio.Queue(maxsize=1)
        hub.subscribers["slow"] = queue
        queue.put_nowait(hub._event("tick", payload=_record(0)))

        await hub._publish(hub._event("tick", payload=_record(1)))
        terminal = queue.get_nowait()
        assert terminal is not None
        assert terminal.event_type == "gap"
        assert terminal.error == "DATA_DROPPED"

        await hub._publish(hub._event("tick", payload=_record(2)))
        assert queue.empty()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("failure", "event_type", "error_code"),
    [
        (DataError("DATA_DROPPED"), "gap", "DATA_DROPPED"),
        (RuntimeError("provider failed"), "error", "SOURCE_UNAVAILABLE"),
    ],
)
def test_hub_maps_provider_failures_to_terminal_events(
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
    event_type: str,
    error_code: str,
) -> None:
    """Known gaps and unknown provider failures terminate explicitly."""

    async def scenario() -> None:
        async def producer() -> AsyncGenerator[TickRecord]:
            if False:
                yield _record(0)
            raise failure

        monkeypatch.setattr(_StreamHub, "_producer", lambda _self: producer())
        request = MarketStreamRequest(
            source_id="mt5",
            symbol="EURUSD",
            mode="ticks",
            timeframe="M1",
            request_id=generate_id("req"),
        )
        hub = _StreamHub(request)
        queue = await hub.subscribe("consumer", None)
        terminal = await asyncio.wait_for(queue.get(), timeout=1)
        assert terminal is not None
        assert terminal.event_type == event_type
        assert terminal.error == error_code
        assert terminal.terminal
        await hub.unsubscribe("consumer")

    asyncio.run(scenario())


def test_public_stream_yields_data_and_cleans_up_final_subscriber(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The package operation owns subscription registration and final cleanup."""

    async def scenario() -> None:
        release = asyncio.Event()

        async def producer() -> AsyncGenerator[TickRecord]:
            yield _record(1)
            await release.wait()

        monkeypatch.setattr(_StreamHub, "_producer", lambda _self: producer())
        _HUBS.clear()
        request = build_market_stream_request(
            source_id="mt5",
            symbol="EURUSD",
            mode="ticks",
            timeframe="M1",
            request_id=generate_id("req"),
        )
        stream = stream_market_data(request)
        event = await asyncio.wait_for(anext(stream), timeout=1)
        assert event.event_type == "tick"
        await stream.aclose()
        assert not next(iter(_HUBS.values())).subscribers
        release.set()
        _HUBS.clear()

    asyncio.run(scenario())


def test_resume_outside_retained_window_fails_closed() -> None:
    """A cursor older or newer than retained history cannot imply continuity."""

    async def scenario() -> None:
        request = MarketStreamRequest(
            source_id="mt5",
            symbol="EURUSD",
            mode="bars",
            timeframe="M5",
            request_id=generate_id("req"),
        )
        hub = _StreamHub(request)
        hub.history.append(hub._event("bar", payload=_record(1)))
        with pytest.raises(DataError, match="STATE_RECOVERY_FAILED"):
            await hub.subscribe("stale", 10)

    asyncio.run(scenario())


def test_hub_registry_evicts_only_inactive_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retained resume state is bounded without evicting an active producer."""
    monkeypatch.setattr(subscriptions, "_STREAM_HUB_LIMIT", 1)
    _HUBS.clear()
    first = MarketStreamRequest(
        source_id="mt5",
        symbol="EURUSD",
        mode="ticks",
        timeframe="M1",
        request_id=generate_id("req"),
    )
    second = first.model_copy(update={"symbol": "GBPUSD"})
    _admit_hub(("mt5", "EURUSD", "ticks", "M1"), first)
    _admit_hub(("mt5", "GBPUSD", "ticks", "M1"), second)
    assert tuple(_HUBS) == (("mt5", "GBPUSD", "ticks", "M1"),)

    _HUBS.clear()
    first_hub = _admit_hub(("mt5", "EURUSD", "ticks", "M1"), first)
    first_hub.subscribers["active"] = asyncio.Queue()
    with pytest.raises(DataError, match="LIMIT_EXCEEDED"):
        _admit_hub(("mt5", "GBPUSD", "ticks", "M1"), second)
    _HUBS.clear()


def _base_event_fields() -> dict[str, Any]:
    """Return one reusable MarketStreamEvent identity/timing fixture.

    Returns:
        Non-payload fields shared by every unified-market-event assertion.
    """
    return {
        "feed_id": "feed-abc",
        "sequence": 0,
        "mode": "ticks",
        "source_id": "mt5",
        "symbol": "EURUSD",
        "timeframe": "M1",
        "occurred_at": _NOW,
        "cursor": "0",
        "request_id": generate_id("req"),
    }


@pytest.mark.parametrize(
    ("event_type", "payload"),
    [
        (
            "trade",
            build_trade_payload(price=1.1000, size=1.0, side="buy", trade_id="T1"),
        ),
        (
            "depth",
            build_depth_update_payload(side="bid", level=0, price=1.1000, size=1.0),
        ),
        ("venue_state", build_venue_state_payload(state="halted", reason="drift")),
        ("halt", build_halt_payload(reason="news pending")),
        (
            "auction",
            build_auction_payload(
                reference_price=1.1000, matched_size=10.0, imbalance=1.0
            ),
        ),
        (
            "corporate_action",
            build_corporate_action_payload(
                action_type="split", effective_date=_NOW, ratio=2.0
            ),
        ),
    ],
)
def test_unified_market_event_accepts_each_new_event_family(
    event_type: str, payload: object
) -> None:
    """Every application Phase 0 event family validates with its own payload."""
    event = MarketStreamEvent(
        event_type=event_type, payload=payload, **_base_event_fields()
    )
    assert event.event_type == event_type
    assert event.payload is payload


def test_unified_market_event_rejects_mismatched_payload_type() -> None:
    """A payload built for one event family cannot validate another."""
    halt_payload = build_halt_payload(reason="news pending")
    with pytest.raises(DataError, match="INVALID_INPUT"):
        MarketStreamEvent(
            event_type="trade", payload=halt_payload, **_base_event_fields()
        )


def test_unified_market_event_rejects_missing_payload_for_new_families() -> None:
    """Every new market-payload event family requires a typed payload."""
    for event_type in (
        "trade",
        "depth",
        "venue_state",
        "halt",
        "auction",
        "corporate_action",
    ):
        with pytest.raises(DataError, match="INVALID_INPUT"):
            MarketStreamEvent(
                event_type=event_type, payload=None, **_base_event_fields()
            )
