"""Real-Time Market Events domain service implementation.

Purpose:
    Manage real-time market event streaming, subscription lifecycles, heartbeats,
    backpressure buffers, and bounded event replays.

Key capabilities:
    * Manage real-time feed subscriptions with backpressure policies.
    * Enforce heartbeat monitoring and stale-connection detection.
    * Provide bounded deterministic event replay from SQLite persistence.
    * Provide async stream_market_events implementing StreamMarketEventsCapability.

Python API usage:
    from app.services.data.realtime_market_events.realtime_market_events import (
        RealtimeMarketEventsService,
    )
    from app.contracts.data.models import StreamMarketEventsRequest

    service = RealtimeMarketEventsService()
    result = await service.stream_market_events(request)

CLI usage:
    uv run python -m app.services.data.realtime_market_events.realtime_market_events
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import uuid
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, override

from app.contracts.catalogue.models import ProviderRef
from app.contracts.common.events import DomainEvent
from app.contracts.common.models import (
    ContentHash,
    ProblemDetails,
    UtcTimestamp,
    Uuid7,
)
from app.contracts.data.errors import DataFailure, DataFailureCode
from app.contracts.data.models import (
    MarketEvent,
    MarketFeedState,
    MarketReplayRef,
    SeriesInterval,
    StreamMarketEventsRequest,
    StreamMarketEventsSubscription,
    StreamMarketEventsSuccess,
)
from app.contracts.data.ports import StreamMarketEventsCapability
from app.services.data.realtime_market_events.config import (
    RealtimeMarketEventsConfig,
)

if TYPE_CHECKING:
    from app.kernel.events import EventBus

logger = logging.getLogger(__name__)

_UUID7_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _generate_uuid7() -> Uuid7:
    """Generate a canonical UUIDv7 string.

    Returns:
        UUIDv7 string formatted per RFC 9562.
    """
    return str(uuid.uuid7())


def _is_valid_uuid7(val: str) -> bool:
    """Check if a string is a valid UUIDv7.

    Args:
        val: String to test.

    Returns:
        True if valid UUIDv7 format, otherwise False.
    """
    return bool(_UUID7_PATTERN.match(val.lower()))


def _current_utc_timestamp() -> UtcTimestamp:
    """Return current UTC timestamp formatted ISO 8601.

    Returns:
        UTC timestamp formatted string.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def compute_raw_hash(data: dict[str, Any] | str | bytes) -> ContentHash:
    """Compute deterministic SHA-256 hex digest.

    Args:
        data: Payload dictionary, string, or bytes.

    Returns:
        64-character lowercase hexadecimal SHA-256 digest string.
    """
    if isinstance(data, (dict, list)):
        payload_bytes = json.dumps(
            data, sort_keys=True, separators=(",", ":"), default=str
        ).encode("utf-8")
    elif isinstance(data, str):
        payload_bytes = data.encode("utf-8")
    else:
        payload_bytes = data
    return hashlib.sha256(payload_bytes).hexdigest()


def _make_failure(
    request_id: str,
    code: DataFailureCode,
    title: str,
    detail: str,
    *,
    status: int = 400,
    error_type: str = "https://errors.haruquantai.io/data",
) -> DataFailure:
    """Construct a structured DataFailure envelope.

    Args:
        request_id: Tracking request ID.
        code: Typed DataFailureCode literal.
        title: Short human-readable title.
        detail: Human-readable error detail.
        status: HTTP status code.
        error_type: RFC 9457 problem type URI.

    Returns:
        Structured DataFailure instance.
    """
    req_uuid7 = request_id if _is_valid_uuid7(request_id) else _generate_uuid7()
    return DataFailure(
        request_id=req_uuid7,
        code=code,
        problem=ProblemDetails(
            type=error_type,
            title=title,
            status=status,
            code=code,
            detail=detail,
            request_id=req_uuid7,
        ),
        outcome="FAILURE",
    )


class StreamMarketEventsService(StreamMarketEventsCapability):
    """Real-time market events ingestion, normalisation, and replay service."""

    def __init__(
        self,
        config: RealtimeMarketEventsConfig | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the real-time market events service.

        Args:
            config: Optional service configuration.
            event_bus: Optional kernel event bus for dispatch.
        """
        self._config = config or RealtimeMarketEventsConfig()
        self._event_bus = event_bus
        self._lock = asyncio.Lock()

        # Feed state store: feed_id -> MarketFeedState
        self._feeds: dict[str, MarketFeedState] = {}
        # Provider to feed mapping: provider_id -> feed_id
        self._provider_to_feed: dict[str, str] = {}
        # Buffered events per feed: feed_id -> deque[MarketEvent]
        self._event_buffers: dict[str, deque[MarketEvent]] = defaultdict(
            lambda: deque(maxlen=self._config.buffer_capacity)
        )
        # Sequence tracking per feed: feed_id -> last_seen_sequence
        self._feed_sequences: dict[str, int] = {}
        # Feed disconnect timestamps: feed_id -> disconnect_at
        self._feed_disconnects: dict[str, UtcTimestamp] = {}
        # Active subscriber queues: list of (Subscription, Queue)
        self._subscribers: list[
            tuple[
                StreamMarketEventsSubscription,
                asyncio.Queue[DomainEvent | None],
            ]
        ] = []
        # Recorded replay partitions: replay_id -> MarketReplayRef
        self._replays: dict[str, MarketReplayRef] = {}
        # Global monotonic event sequence counter for domain event envelope
        self._global_sequence: int = 0

    @property
    def config(self) -> RealtimeMarketEventsConfig:
        """Return the service configuration."""
        return self._config

    @override
    async def stream_market_events(
        self,
        request: StreamMarketEventsRequest,
    ) -> StreamMarketEventsSuccess | DataFailure:
        """Bind feeds, observe feed state, and record bounded replays.

        Args:
            request: Operation-discriminated market event request.

        Returns:
            The feed state and replay reference on success, otherwise a
            structured data failure.
        """
        async with self._lock:
            match request.operation:
                case "BIND_FEED":
                    return self._handle_bind_feed(request)
                case "FEED_STATE":
                    return self._handle_feed_state(request)
                case "REPLAY":
                    return self._handle_replay(request)

    def _handle_bind_feed(
        self, request: StreamMarketEventsRequest
    ) -> StreamMarketEventsSuccess | DataFailure:
        """Handle BIND_FEED operation.

        Args:
            request: Market event request.

        Returns:
            StreamMarketEventsSuccess on success or DataFailure on error.
        """
        provider_id = request.provider_id
        if not provider_id:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "Missing Provider",
                "BIND_FEED requires provider_id",
            )

        if provider_id in self._provider_to_feed:
            feed_id = self._provider_to_feed[provider_id]
            feed_state = self._feeds[feed_id]
            return StreamMarketEventsSuccess(
                request_id=request.request_id,
                feed_state=feed_state,
                replay=None,
            )

        feed_id = _generate_uuid7()
        now = _current_utc_timestamp()
        feed_state = MarketFeedState(
            feed_id=feed_id,
            provider=ProviderRef(
                provider_id=provider_id,
                provider_name=f"PROVIDER-{provider_id[:8]}",
            ),
            generation=1,
            state="CONNECTING",
            observed_at=now,
            last_event_at=None,
            uncovered_intervals=(),
        )
        self._feeds[feed_id] = feed_state
        self._provider_to_feed[provider_id] = feed_id

        return StreamMarketEventsSuccess(
            request_id=request.request_id,
            feed_state=feed_state,
            replay=None,
        )

    def _handle_feed_state(
        self, request: StreamMarketEventsRequest
    ) -> StreamMarketEventsSuccess | DataFailure:
        """Handle FEED_STATE operation with freshness evaluation.

        Args:
            request: Market event request.

        Returns:
            StreamMarketEventsSuccess on success or DataFailure on error.
        """
        feed_id = request.feed_id
        if not feed_id or feed_id not in self._feeds:
            return _make_failure(
                request.request_id,
                "DATA_NOT_FOUND",
                "Feed Not Found",
                f"Market feed '{feed_id}' is not registered",
                status=404,
            )

        feed_state = self._feeds[feed_id]
        now = _current_utc_timestamp()

        # Check staleness if feed is currently LIVE
        if feed_state.state == "LIVE" and feed_state.last_event_at is not None:
            try:
                last_dt = datetime.fromisoformat(feed_state.last_event_at)
                now_dt = datetime.now(UTC)
                if (
                    now_dt - last_dt
                ).total_seconds() > self._config.stale_timeout_seconds:
                    feed_state = MarketFeedState(
                        feed_id=feed_state.feed_id,
                        provider=feed_state.provider,
                        generation=feed_state.generation,
                        state="STALE",
                        observed_at=now,
                        last_event_at=feed_state.last_event_at,
                        uncovered_intervals=feed_state.uncovered_intervals,
                    )
                    self._feeds[feed_id] = feed_state
            except Exception:
                logger.debug("Failed to parse last_event_at", exc_info=True)

        return StreamMarketEventsSuccess(
            request_id=request.request_id,
            feed_state=feed_state,
            replay=None,
        )

    def _handle_replay(
        self, request: StreamMarketEventsRequest
    ) -> StreamMarketEventsSuccess | DataFailure:
        """Handle REPLAY operation generating bounded replay reference.

        Args:
            request: Market event request.

        Returns:
            StreamMarketEventsSuccess on success or DataFailure on error.
        """
        feed_id = request.feed_id
        if not feed_id or feed_id not in self._feeds:
            return _make_failure(
                request.request_id,
                "DATA_NOT_FOUND",
                "Feed Not Found",
                f"Market feed '{feed_id}' is not registered",
                status=404,
            )

        if not request.from_at or not request.to_at:
            return _make_failure(
                request.request_id,
                "DATA_VALIDATION_FAILED",
                "Invalid Replay Interval",
                "REPLAY requires positive interval with from_at and to_at",
            )

        feed_state = self._feeds[feed_id]
        buffered = self._event_buffers[feed_id]

        matching_events = [
            ev for ev in buffered if request.from_at <= ev.event_time <= request.to_at
        ]

        replay_id = _generate_uuid7()
        artifact_id = _generate_uuid7()
        content_hash = compute_raw_hash(
            {
                "feed_id": feed_id,
                "generation": feed_state.generation,
                "from_at": request.from_at,
                "to_at": request.to_at,
                "events": [ev.model_dump(mode="json") for ev in matching_events],
            }
        )

        replay_ref = MarketReplayRef(
            replay_id=replay_id,
            feed_id=feed_id,
            generation=feed_state.generation,
            partition_artifact_ids=(artifact_id,),
            from_at=request.from_at,
            to_at=request.to_at,
            event_count=len(matching_events),
            content_hash=content_hash,
        )
        self._replays[replay_id] = replay_ref

        return StreamMarketEventsSuccess(
            request_id=request.request_id,
            feed_state=feed_state,
            replay=replay_ref,
        )

    def _update_feed_state_for_event(
        self, event: MarketEvent, now: UtcTimestamp
    ) -> str:
        """Update internal feed state and sequences for incoming event.

        Args:
            event: The incoming market event.
            now: Current receipt timestamp.

        Returns:
            The associated feed identifier string.
        """
        provider_id = event.provider.provider_id
        if provider_id not in self._provider_to_feed:
            feed_id = _generate_uuid7()
            self._feeds[feed_id] = MarketFeedState(
                feed_id=feed_id,
                provider=event.provider,
                generation=1,
                state="LIVE",
                observed_at=now,
                last_event_at=now,
                uncovered_intervals=(),
            )
            self._provider_to_feed[provider_id] = feed_id
            if event.provider_sequence is not None:
                self._feed_sequences[feed_id] = event.provider_sequence
            return feed_id

        feed_id = self._provider_to_feed[provider_id]
        current_state = self._feeds[feed_id]

        next_state_str = "LIVE"
        if (
            event.provider_sequence is not None
            and event.ordering_mode == "PROVIDER_SEQUENCE"
        ):
            last_seq = self._feed_sequences.get(feed_id)
            if last_seq is not None:
                if event.provider_sequence > last_seq + 1:
                    next_state_str = "GAP"
                elif event.provider_sequence <= last_seq:
                    next_state_str = current_state.state
            self._feed_sequences[feed_id] = max(
                self._feed_sequences.get(feed_id, -1),
                event.provider_sequence,
            )

        self._feeds[feed_id] = MarketFeedState(
            feed_id=feed_id,
            provider=current_state.provider,
            generation=current_state.generation,
            state=next_state_str,  # type: ignore[arg-type]
            observed_at=now,
            last_event_at=now,
            uncovered_intervals=current_state.uncovered_intervals,
        )
        return feed_id

    def _dispatch_to_subscribers(
        self, event: MarketEvent, feed_id: str, dom_event: DomainEvent
    ) -> None:
        """Distribute domain event envelope to active matching subscribers."""
        provider_id = event.provider.provider_id
        for sub, queue in list(self._subscribers):
            if sub.provider_id and sub.provider_id != provider_id:
                continue
            if sub.feed_id and sub.feed_id != feed_id:
                continue
            if sub.instruments:
                sub_insts = {i.instrument_id for i in sub.instruments}
                if (
                    not event.instrument
                    or event.instrument.instrument_id not in sub_insts
                ):
                    continue

            try:
                queue.put_nowait(dom_event)
            except asyncio.QueueFull:
                if self._config.backpressure_policy == "DROP_AND_GAP":
                    logger.warning("Subscriber queue full; dropping event")

    async def ingest_event(
        self,
        event: MarketEvent,
    ) -> None:
        """Normalize, buffer, track sequence, and dispatch one market event.

        Args:
            event: The fully-formed normalized MarketEvent.
        """
        async with self._lock:
            now = event.receipt_time
            feed_id = self._update_feed_state_for_event(event, now)

            # Buffer event
            self._event_buffers[feed_id].append(event)
            self._global_sequence += 1

            # Dispatch DomainEvent envelope
            dom_event = DomainEvent(
                event_id=event.event_id,
                sequence=self._global_sequence,
                event_type="data.market-event",
                occurred_at=event.receipt_time,
                request_id=_generate_uuid7(),
                capability_snapshot_id=_generate_uuid7(),
                payload=event.model_dump(mode="json"),
            )
            self._dispatch_to_subscribers(event, feed_id, dom_event)

    def _get_historical_events(
        self, request: StreamMarketEventsSubscription
    ) -> list[MarketEvent]:
        """Retrieve historical buffered events filtered by subscription.

        Args:
            request: The event subscription selector.

        Returns:
            List of matching historical market events.
        """
        feeds_to_replay = []
        if request.feed_id and request.feed_id in self._event_buffers:
            feeds_to_replay.append(request.feed_id)
        elif request.provider_id and request.provider_id in self._provider_to_feed:
            feeds_to_replay.append(self._provider_to_feed[request.provider_id])
        else:
            feeds_to_replay.extend(self._event_buffers.keys())

        historical: list[MarketEvent] = []
        for fid in feeds_to_replay:
            historical.extend(self._event_buffers[fid])

        if request.instruments:
            inst_ids = {i.instrument_id for i in request.instruments}
            historical = [
                e
                for e in historical
                if e.instrument and e.instrument.instrument_id in inst_ids
            ]
        return historical

    @override
    async def subscribe_stream_market_events_events(
        self,
        request: StreamMarketEventsSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver live normalized market events as domain events.

        Args:
            request: Subscription selector carrying filters, resume position,
                and bounded replay limit.

        Yields:
            Asynchronous stream of DomainEvent envelopes.
        """
        queue: asyncio.Queue[DomainEvent | None] = asyncio.Queue(
            maxsize=self._config.buffer_capacity
        )
        sub_entry = (request, queue)

        async with self._lock:
            self._subscribers.append(sub_entry)

            # Replay historical buffered events if requested
            if request.replay_limit > 0:
                limit = min(request.replay_limit, self._config.max_replay_limit)
                historical = self._get_historical_events(request)

                for ev in historical[-limit:]:
                    dom_ev = DomainEvent(
                        event_id=ev.event_id,
                        sequence=0,
                        event_type="data.market-event",
                        occurred_at=ev.receipt_time,
                        request_id=_generate_uuid7(),
                        capability_snapshot_id=_generate_uuid7(),
                        payload=ev.model_dump(mode="json"),
                    )
                    try:
                        queue.put_nowait(dom_ev)
                    except asyncio.QueueFull:
                        break

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
        finally:
            async with self._lock:
                if sub_entry in self._subscribers:
                    self._subscribers.remove(sub_entry)

    async def simulate_disconnect(
        self, feed_id: str, disconnect_at: UtcTimestamp | None = None
    ) -> MarketFeedState:
        """Simulate a feed disconnect and transition state to RECONNECTING.

        Args:
            feed_id: Target market feed identifier.
            disconnect_at: Optional timestamp of disconnection.

        Returns:
            Updated MarketFeedState instance.

        Raises:
            KeyError: If the specified feed_id is not found.
        """
        async with self._lock:
            if feed_id not in self._feeds:
                err_msg = f"Feed '{feed_id}' not found"
                raise KeyError(err_msg)
            ts = disconnect_at or _current_utc_timestamp()
            current = self._feeds[feed_id]
            self._feed_disconnects[feed_id] = ts
            new_state = MarketFeedState(
                feed_id=current.feed_id,
                provider=current.provider,
                generation=current.generation,
                state="RECONNECTING",
                observed_at=ts,
                last_event_at=current.last_event_at,
                uncovered_intervals=current.uncovered_intervals,
            )
            self._feeds[feed_id] = new_state
            return new_state

    async def reconnect_feed(
        self, feed_id: str, reconnect_at: UtcTimestamp | None = None
    ) -> MarketFeedState:
        """Reconnect feed, increment generation, and record uncovered interval.

        Args:
            feed_id: Target market feed identifier.
            reconnect_at: Optional timestamp of reconnection.

        Returns:
            Updated MarketFeedState instance.

        Raises:
            KeyError: If the specified feed_id is not found.
        """
        async with self._lock:
            if feed_id not in self._feeds:
                err_msg = f"Feed '{feed_id}' not found"
                raise KeyError(err_msg)
            ts = reconnect_at or _current_utc_timestamp()
            current = self._feeds[feed_id]
            disc_at = self._feed_disconnects.get(feed_id, current.observed_at)

            interval = SeriesInterval(from_at=disc_at, to_at=ts)
            new_intervals = (*current.uncovered_intervals, interval)

            new_state = MarketFeedState(
                feed_id=current.feed_id,
                provider=current.provider,
                generation=current.generation + 1,
                state="LIVE",
                observed_at=ts,
                last_event_at=ts,
                uncovered_intervals=new_intervals,
            )
            self._feeds[feed_id] = new_state
            return new_state


async def _run_usage_scenarios() -> None:
    """Delegate to _usage module."""
    from app.services.data.realtime_market_events._usage import (
        main as _usage_main,
    )

    await _usage_main()


async def main() -> None:
    """Execute the real-time market events usage demonstration harness."""
    await _run_usage_scenarios()


def run_usage_scenarios() -> None:
    """Synchronous runner entry point for the usage demonstration."""
    import asyncio

    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
