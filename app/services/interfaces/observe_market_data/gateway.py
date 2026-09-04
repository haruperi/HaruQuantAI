"""Market data observation gateway: the capability provider.

Purpose:
    Project the Data-owned live market event stream
    (``data.stream-market-events@1``) into the Interfaces observation
    contract: bounded market tick snapshots with source identity,
    monotonic sequence, gap counting, and honest staleness, plus
    resumable filtered observation event delivery.

Key capabilities:
    * Consume the provider subscription in a supervised gateway task.
    * Project the latest quote per symbol without inventing values.
    * Report stale snapshots with explicit reasons and never fabricate
      freshness after provider loss.
    * Delegate resumable, symbol-filtered event delivery to the provider.

Python API usage:
    gateway = MarketDataGateway(provider, ObserveMarketDataConfig())
    await gateway.run()
    result = await gateway.observe_market_data(request)

CLI usage:
    uv run python -m app.services.interfaces.observe_market_data.gateway
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, NoReturn
from uuid import uuid7

from app.contracts.common.events import DomainEvent
from app.contracts.common.models import ProblemDetails
from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.contracts.data.models import (
    StreamMarketEventsRequest,
    StreamMarketEventsSubscription,
)
from app.contracts.interfaces.errors import InterfaceFailure, InterfaceFailureCode
from app.contracts.interfaces.models import (
    MarketTickQuote,
    MarketTickSnapshot,
    ObserveMarketDataEventSubscription,
    ObserveMarketDataRequest,
    ObserveMarketDataSuccess,
)
from app.services.interfaces.observe_market_data.config import ObserveMarketDataConfig

if TYPE_CHECKING:
    from app.contracts.data.ports import StreamMarketEventsCapability

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
_PROVIDER_SOURCE_ID = STREAM_MARKET_EVENTS_CAPABILITY.identifier
_EXPECTED_FINAL_SEQUENCE = 4


def _utc_now() -> datetime:
    """Return the current UTC instant.

    Returns:
        Timezone-aware UTC datetime.
    """
    return datetime.now(UTC)


def _format_timestamp(moment: datetime) -> str:
    """Format a UTC datetime as a canonical wire timestamp.

    Args:
        moment: Timezone-aware UTC datetime.

    Returns:
        Fixed-width wire timestamp string.
    """
    return moment.astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _parse_timestamp(value: str) -> datetime:
    """Parse a canonical wire timestamp into a UTC datetime.

    Args:
        value: Fixed-width wire timestamp string.

    Returns:
        Timezone-aware UTC datetime.
    """
    return datetime.strptime(value, _TIMESTAMP_FORMAT).replace(tzinfo=UTC)


def _failure(
    request_id: str,
    code: InterfaceFailureCode,
    title: str,
    detail: str,
    status: int,
) -> InterfaceFailure:
    """Build a structured gateway failure envelope.

    Args:
        request_id: Echoed request identifier.
        code: Closed interface failure code.
        title: Short failure title.
        detail: Bounded human-readable failure detail.
        status: HTTP-equivalent status code.

    Returns:
        Structured InterfaceFailure envelope.
    """
    return InterfaceFailure(
        request_id=request_id,
        code=code,
        problem=ProblemDetails(
            title=title,
            status=status,
            code=code,
            detail=detail,
        ),
    )


def _quote_source(payload: Mapping[str, object]) -> Mapping[str, object]:
    """Select the quote-carrying mapping inside one provider payload.

    Providers may emit flat quote payloads or normalized ``MarketEvent``
    envelopes whose quote fields live under ``values``; both are accepted.

    Args:
        payload: Provider event payload.

    Returns:
        The mapping to read quote fields from.
    """
    values = payload.get("values")
    if isinstance(values, dict):
        return values
    return payload


def _project_quote(event: DomainEvent) -> MarketTickQuote | None:
    """Project one provider event payload into a quote record.

    Args:
        event: Provider domain event.

    Returns:
        The projected quote, or None when the payload does not carry a
        projectable symbol/bid/ask shape.
    """
    source = _quote_source(event.payload)
    symbol = source.get("symbol")
    bid = source.get("bid")
    ask = source.get("ask")
    if not isinstance(symbol, str) or not symbol:
        return None
    if isinstance(bid, bool) or not isinstance(bid, (int, float, str)):
        return None
    if isinstance(ask, bool) or not isinstance(ask, (int, float, str)):
        return None
    try:
        return MarketTickQuote(
            symbol=symbol,
            timestamp=event.occurred_at,
            bid=str(bid),
            ask=str(ask),
        )
    except ValueError:
        return None


def _matches_filter(symbols: tuple[str, ...], event: DomainEvent) -> bool:
    """Check one event against the subscription symbol filter.

    Args:
        symbols: Subscription filter; empty selects every event.
        event: Provider domain event.

    Returns:
        True when the event matches the filter.
    """
    if not symbols:
        return True
    payload_symbol = _quote_source(event.payload).get("symbol")
    return isinstance(payload_symbol, str) and payload_symbol in frozenset(symbols)


async def _aclose(stream: AsyncIterator[DomainEvent]) -> None:
    """Close a provider iterator when it supports aclose.

    Args:
        stream: Provider async iterator to release.
    """
    close = getattr(stream, "aclose", None)
    if close is not None:
        await close()


class MarketDataGateway:
    """ObserveMarketDataCapability provider for one mounted generation.

    The gateway resolves the Data-owned stream capability through the
    feature context, never imports a Data or broker implementation, and
    adds no business policy: it projects provider events into the
    observation contract and reports absence truthfully.
    """

    def __init__(
        self,
        provider: StreamMarketEventsCapability,
        config: ObserveMarketDataConfig,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Assemble the gateway around the resolved provider.

        Args:
            provider: Active data.stream-market-events provider.
            config: Feature configuration with staleness and bounds.
            clock: Injectable UTC clock for deterministic staleness.
        """
        self._provider = provider
        self._config = config
        self._clock = clock or _utc_now
        self._quotes: dict[str, MarketTickQuote] = {}
        self._sequence = 0
        self._gap_count = 0
        self._last_event_at: datetime | None = None
        self._degraded_reason: str | None = None
        self._closed = False

    @property
    def config(self) -> ObserveMarketDataConfig:
        """Return the validated gateway configuration."""
        return self._config

    @property
    def degraded_reason(self) -> str | None:
        """Return the provider-loss reason when the gateway is degraded."""
        return self._degraded_reason

    async def run(self) -> None:
        """Consume the provider subscription until closed or provider loss.

        Normal provider termination degrades the gateway (snapshots keep
        reporting the last known truth as stale); a provider failure is
        recorded and re-raised so kernel reconciliation owns the runtime
        failure.
        """
        provider_stream = self._provider.subscribe_stream_market_events_events(
            StreamMarketEventsSubscription()
        )
        try:
            async for event in provider_stream:
                if self._closed:
                    return
                self._apply(event)
        except Exception:
            self._degraded_reason = "market event provider stream failed"
            raise
        finally:
            await _aclose(provider_stream)
        self._degraded_reason = "market event provider stream ended"

    async def observe_market_data(
        self,
        request: ObserveMarketDataRequest,
    ) -> ObserveMarketDataSuccess | InterfaceFailure:
        """Project the current market tick snapshot.

        Args:
            request: Operation-discriminated observation request.

        Returns:
            The snapshot projection on success, otherwise a structured
            interface failure.
        """
        if self._closed:
            return _failure(
                request.request_id,
                "CAPABILITY_UNAVAILABLE",
                "Gateway unavailable",
                "The market observation gateway is disposed.",
                503,
            )
        if len(request.symbols) > self._config.max_symbols:
            return _failure(
                request.request_id,
                "INTERFACE_VALIDATION_FAILED",
                "Symbol filter too large",
                "The requested symbol filter exceeds max_symbols="
                f"{self._config.max_symbols}.",
                400,
            )
        return ObserveMarketDataSuccess(
            request_id=request.request_id,
            snapshot=self._project(request),
        )

    def subscribe_observe_market_data_events(
        self,
        request: ObserveMarketDataEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver filtered, resumable market observation events.

        Args:
            request: Subscription selector with symbol filter, resume
                cursor, and bounded replay limit.

        Returns:
            Async iterator of provider market events in the common
            domain event envelope.
        """
        return self._stream(request)

    async def _stream(
        self,
        request: ObserveMarketDataEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Iterate provider events filtered by the subscription selector.

        Yields:
            Provider market events matching the subscription filter.
        """
        provider_request = StreamMarketEventsSubscription(
            resume_event_id=request.resume_event_id,
            replay_limit=request.replay_limit,
        )
        provider_stream = self._provider.subscribe_stream_market_events_events(
            provider_request
        )
        try:
            async for event in provider_stream:
                if self._closed:
                    return
                if _matches_filter(request.symbols, event):
                    yield event
        finally:
            await _aclose(provider_stream)

    def _apply(self, event: DomainEvent) -> None:
        """Apply one provider event to the observation buffer.

        Sequence discontinuities are counted as gaps; payloads without a
        projectable symbol/bid/ask shape advance the sequence without a
        quote projection and never invent values.
        """
        if event.sequence > self._sequence:
            if self._sequence and event.sequence > self._sequence + 1:
                self._gap_count += event.sequence - self._sequence - 1
            self._sequence = event.sequence
            self._last_event_at = _parse_timestamp(event.occurred_at)
        quote = _project_quote(event)
        if quote is not None:
            self._quotes[quote.symbol] = quote

    def _project(self, request: ObserveMarketDataRequest) -> MarketTickSnapshot:
        """Build the current snapshot projection.

        Args:
            request: Observation request carrying the symbol filter.

        Returns:
            Snapshot with source identity, sequence, gaps, and staleness.
        """
        filter_symbols = frozenset(request.symbols)
        quotes = tuple(
            self._quotes[symbol]
            for symbol in sorted(self._quotes)
            if not filter_symbols or symbol in filter_symbols
        )
        stale, reason = self._staleness()
        occurred = self._last_event_at or self._clock()
        return MarketTickSnapshot(
            sequence=self._sequence,
            source_id=_PROVIDER_SOURCE_ID,
            occurred_at=_format_timestamp(occurred),
            stale=stale,
            stale_reason=reason,
            gap=self._gap_count,
            quotes=quotes,
        )

    def _staleness(self) -> tuple[bool, str | None]:
        """Evaluate snapshot staleness honestly.

        Returns:
            (stale, reason) where a stale snapshot always carries an
            explicit reason.
        """
        if self._degraded_reason is not None:
            return True, self._degraded_reason
        if self._last_event_at is None:
            return True, "no market events received yet"
        age = (self._clock() - self._last_event_at).total_seconds()
        if age > self._config.stale_after_seconds:
            message = (
                f"last market event was {age:.3f}s ago, exceeding "
                f"stale_after_seconds={self._config.stale_after_seconds}"
            )
            return True, message
        return False, None

    def close(self) -> None:
        """Dispose the gateway; safe to call repeatedly."""
        self._quotes.clear()
        self._closed = True


class _ScriptedMarketEventProvider:
    """Bounded in-memory provider for the usage demonstration."""

    def __init__(self, events: tuple[DomainEvent, ...]) -> None:
        """Store the scripted events for one subscription each."""
        self._events = events

    async def stream_market_events(
        self,
        _request: StreamMarketEventsRequest,
    ) -> NoReturn:
        """Not exercised by the demonstration.

        Raises:
            NotImplementedError: The demonstration never binds feeds.
        """
        raise NotImplementedError("stream operations are not exercised")

    def subscribe_stream_market_events_events(
        self,
        _request: StreamMarketEventsSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Yield the scripted events once.

        Returns:
            Async iterator over the scripted events.
        """
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[DomainEvent]:
        """Yield the scripted events in order."""
        for event in self._events:
            yield event


def _scripted_event(
    sequence: int,
    symbol: str,
    bid: str,
    ask: str,
) -> DomainEvent:
    """Build one scripted provider event.

    Args:
        sequence: Provider event sequence number.
        symbol: Observed instrument symbol.
        bid: Decimal bid string.
        ask: Decimal ask string.

    Returns:
        Domain event in the common envelope.
    """
    return DomainEvent(
        event_id=str(uuid7()),
        sequence=sequence,
        event_type="market.tick",
        occurred_at=_format_timestamp(_utc_now()),
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        payload={"symbol": symbol, "bid": bid, "ask": ask},
    )


def _snapshot_request(symbols: tuple[str, ...] = ()) -> ObserveMarketDataRequest:
    """Build the demonstration snapshot request.

    Args:
        symbols: Optional bounded symbol filter.

    Returns:
        Operation-discriminated SNAPSHOT request.
    """
    return ObserveMarketDataRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="SNAPSHOT",
        symbols=symbols,
    )


def _require_snapshot(
    result: ObserveMarketDataSuccess | InterfaceFailure,
) -> MarketTickSnapshot:
    """Extract the snapshot from a demonstration result.

    Args:
        result: Gateway observation result.

    Returns:
        The projected snapshot.

    Raises:
        TypeError: When the result is a failure without a snapshot.
    """
    if not isinstance(result, ObserveMarketDataSuccess) or result.snapshot is None:
        raise TypeError("usage verification: snapshot missing")
    return result.snapshot


async def _run_usage_example() -> None:
    """Run the bounded public usage demonstration.

    Raises:
        RuntimeError: If any verified behavior differs from the contract.
        TypeError: If a verification result has an unexpected type.
    """
    events = (
        _scripted_event(1, "EURUSD", "1.085", "1.0852"),
        _scripted_event(2, "GBPUSD", "1.2693", "1.2695"),
        _scripted_event(4, "EURUSD", "1.0851", "1.0853"),
    )
    provider = _ScriptedMarketEventProvider(events)
    gateway = MarketDataGateway(
        provider,
        ObserveMarketDataConfig(stale_after_seconds=5_000.0),
    )
    await gateway.run()
    if gateway.degraded_reason is None:
        raise RuntimeError("usage verification: provider loss not observed")

    snapshot = _require_snapshot(await gateway.observe_market_data(_snapshot_request()))
    if snapshot.sequence != _EXPECTED_FINAL_SEQUENCE or snapshot.gap != 1:
        raise RuntimeError("usage verification: sequence or gap mismatch")
    if snapshot.source_id != "data.stream-market-events@1":
        raise RuntimeError("usage verification: source identity mismatch")
    if not snapshot.stale or snapshot.stale_reason is None:
        raise RuntimeError("usage verification: degraded staleness missing")
    if [quote.symbol for quote in snapshot.quotes] != ["EURUSD", "GBPUSD"]:
        raise RuntimeError("usage verification: quote projection mismatch")

    filtered = _require_snapshot(
        await gateway.observe_market_data(_snapshot_request(("GBPUSD",)))
    )
    if [quote.symbol for quote in filtered.quotes] != ["GBPUSD"]:
        raise RuntimeError("usage verification: symbol filter mismatch")

    gateway.close()
    closed = await gateway.observe_market_data(_snapshot_request())
    if not isinstance(closed, InterfaceFailure):
        raise TypeError("usage verification: disposal did not fail closed")
    print(
        "Usage verification passed: "
        f"sequence={snapshot.sequence} gap={snapshot.gap} "
        f"quotes={len(snapshot.quotes)} stale=True "
        f"closed_code={closed.code}"
    )


if __name__ == "__main__":
    asyncio.run(_run_usage_example())
