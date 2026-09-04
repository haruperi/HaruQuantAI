"""Authenticated MT5 snapshot bridge listener.

Implements the ``haruquant.mt5.snapshot.v2`` line protocol served to the
MetaTrader 5 ``TickBridge.mq5`` expert (scripts/integrations/mt5/):

* The EA connects as a TCP client and sends one ``hello`` frame carrying its
  source identity and authentication token.
* A hello with the expected protocol, source ID, and token is answered with
  one ``set_symbols`` command; only then does the EA stream ``snapshot``
  frames (one latest quote per configured symbol per interval).
* Every quote in an accepted snapshot is normalized into one
  :class:`~app.contracts.data.models.MarketEvent` and ingested into the
  real-time stream service, which fans the events out to every subscriber.

The listener fails closed: a hello that does not match the configured source
ID or token closes the connection without acknowledging, and frames received
before a valid hello are rejected the same way. Book and heartbeat frames are
accepted and logged at debug level; depth-of-market streaming is not part of
this bridge yet.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, TypeGuard

from app.contracts.catalogue.models import ProviderRef
from app.contracts.data.models import MarketEvent

if TYPE_CHECKING:
    from app.services.data.realtime_market_events.realtime_market_events import (
        StreamMarketEventsService,
    )

logger = logging.getLogger(__name__)

#: Wire protocol identifier shared with the EA.
PROTOCOL: Final = "haruquant.mt5.snapshot.v2"

#: Upper bound on one line frame, mirroring the EA's own receive buffer cap.
_MAX_LINE_BYTES: Final = 1_048_576

#: Timestamp format shared with the stream service's receipt timestamps.
_TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%S.%fZ"


@dataclass(frozen=True, slots=True)
class SnapshotBridgeSettings:
    """Runtime settings for one bridge listener generation."""

    host: str = "127.0.0.1"
    port: int = 9001
    source_id: str = "mt5-terminal-1"
    auth_token: str = ""
    symbols: tuple[str, ...] = ()


def _utc_now_timestamp() -> str:
    """Return the current UTC instant in the contract timestamp format."""
    return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def _ms_to_timestamp(time_msc: object) -> str | None:
    """Convert one broker-normalized UTC millisecond epoch to ISO-8601.

    Args:
        time_msc: Milliseconds since the Unix epoch, or None.

    Returns:
        ISO-8601 UTC timestamp string, or None when the value is not a
        positive number.
    """
    if isinstance(time_msc, bool) or not isinstance(time_msc, (int, float)):
        return None
    if time_msc <= 0:
        return None
    return datetime.fromtimestamp(time_msc / 1000, tz=UTC).strftime(_TIMESTAMP_FORMAT)


def _numeric(value: object) -> bool:
    """Report whether one value is a real number usable as a quote field."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: object) -> TypeGuard[int]:
    """Report whether one value is a real integer (bools excluded)."""
    return isinstance(value, int) and not isinstance(value, bool)


class Mt5SnapshotBridgeServer:
    """Lifecycle-owned TCP listener for authenticated MT5 snapshot streams.

    The server is inert until :meth:`start` binds its socket and stops
    accepting new connections after :meth:`stop`. Failure to bind is
    reported to the caller so the owning feature can decide whether to
    continue without live snapshots.
    """

    def __init__(
        self,
        service: StreamMarketEventsService,
        settings: SnapshotBridgeSettings,
    ) -> None:
        """Assemble the bridge around the ingestion service.

        Args:
            service: Real-time stream service receiving normalized events.
            settings: Validated bridge runtime settings.
        """
        self._service = service
        self._settings = settings
        self._server: asyncio.AbstractServer | None = None
        self._provider = ProviderRef(
            provider_id=str(uuid.uuid7()),
            provider_name=f"mt5-snapshot-bridge:{settings.source_id}",
        )

    @property
    def provider_id(self) -> str:
        """Return the stable provider identity used for ingested events."""
        return self._provider.provider_id

    async def start(self) -> None:
        """Bind the listener socket and begin accepting EA connections.

        Raises:
            OSError: When the configured address cannot be bound.
        """
        self._server = await asyncio.start_server(
            self._handle_client,
            host=self._settings.host,
            port=self._settings.port,
            limit=_MAX_LINE_BYTES,
        )
        logger.info(
            "MT5 snapshot bridge listening on %s:%s (source %s)",
            self._settings.host,
            self._settings.port,
            self._settings.source_id,
        )

    async def stop(self) -> None:
        """Stop accepting connections and release the listener socket."""
        server, self._server = self._server, None
        if server is not None:
            server.close()
            await server.wait_closed()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Serve one EA connection through the v2 line protocol.

        Args:
            reader: Reader side of the accepted connection.
            writer: Writer side of the accepted connection.
        """
        peer = writer.get_extra_info("peername")
        authenticated = False
        try:
            while True:
                raw = await reader.readuntil(b"\n")
                try:
                    frame = json.loads(raw.decode("utf-8"))
                except UnicodeDecodeError, ValueError:
                    logger.warning("MT5 bridge frame from %s is not JSON", peer)
                    break
                if not isinstance(frame, dict):
                    logger.warning("MT5 bridge frame from %s is not an object", peer)
                    break
                continue_loop, authenticated = await self._dispatch_frame(
                    frame, authenticated, writer, peer
                )
                if not continue_loop:
                    break
        except asyncio.IncompleteReadError:
            logger.debug("MT5 bridge connection %s closed by peer", peer)
        except asyncio.LimitOverrunError:
            logger.warning("MT5 bridge line from %s exceeds bound", peer)
        finally:
            writer.close()
            with contextlib.suppress(ConnectionError, OSError):
                await writer.wait_closed()

    async def _dispatch_frame(
        self,
        frame: dict[str, Any],
        authenticated: bool,
        writer: asyncio.StreamWriter,
        peer: object,
    ) -> tuple[bool, bool]:
        """Apply one parsed frame to the connection state.

        Args:
            frame: Parsed JSON frame object.
            authenticated: Whether the connection is authenticated.
            writer: Connection writer used for hello replies.
            peer: Peer identity for diagnostics.

        Returns:
            Tuple of (continue-serving, authenticated) state after the frame.
        """
        frame_type = frame.get("type")
        if frame_type == "hello":
            hello_ok = self._handle_hello(frame, writer, peer)
            return hello_ok, hello_ok
        if not authenticated:
            logger.warning("MT5 bridge frame from %s before authentication", peer)
            return False, authenticated
        if frame_type == "snapshot":
            await self._handle_snapshot(frame)
            return True, authenticated
        if frame_type in ("book", "heartbeat", "symbols_applied"):
            logger.debug("MT5 bridge %s frame from %s", frame_type, peer)
            return True, authenticated
        logger.debug(
            "MT5 bridge ignored unknown frame type %r from %s", frame_type, peer
        )
        return True, authenticated

    def _handle_hello(
        self,
        frame: dict[str, Any],
        writer: asyncio.StreamWriter,
        peer: object,
    ) -> bool:
        """Validate one hello frame and command the symbol set on success.

        Args:
            frame: Parsed hello frame.
            writer: Connection writer used for the set_symbols reply.
            peer: Peer identity for diagnostics.

        Returns:
            True when the hello authenticated the connection.
        """
        if frame.get("protocol") != PROTOCOL:
            logger.warning("MT5 bridge hello from %s has unknown protocol", peer)
            return False
        if frame.get("source_id") != self._settings.source_id:
            logger.warning("MT5 bridge hello from %s has unexpected source", peer)
            return False
        token = frame.get("token")
        if not isinstance(token, str) or token != self._settings.auth_token:
            logger.warning("MT5 bridge hello from %s failed authentication", peer)
            return False
        symbols = self._settings.symbols or self._requested_symbols(frame)
        # The EA parses this frame with substring markers, so the JSON must
        # stay compact: "revision":1 and "symbols":["A","B"] without spaces.
        reply = json.dumps(
            {
                "type": "set_symbols",
                "protocol": PROTOCOL,
                "revision": 1,
                "symbols": list(symbols),
            },
            separators=(",", ":"),
        )
        writer.write((reply + "\n").encode("utf-8"))
        logger.info(
            "MT5 bridge authenticated source %s from %s for %d symbols",
            self._settings.source_id,
            peer,
            len(symbols),
        )
        return True

    @staticmethod
    def _requested_symbols(frame: dict[str, Any]) -> tuple[str, ...]:
        """Extract the hello's requested symbol list when well-formed.

        Args:
            frame: Parsed hello frame.

        Returns:
            Requested symbols, or an empty tuple when absent or malformed.
        """
        requested = frame.get("symbols")
        if isinstance(requested, list) and all(
            isinstance(item, str) and item for item in requested
        ):
            return tuple(requested)
        return ()

    async def _handle_snapshot(self, frame: dict[str, Any]) -> None:
        """Normalize one snapshot frame into ingested market events.

        Args:
            frame: Parsed snapshot frame carrying quotes and errors.
        """
        quotes = frame.get("quotes")
        if not isinstance(quotes, list):
            return
        sequence = frame.get("sequence")
        for quote in quotes:
            if not isinstance(quote, dict):
                continue
            symbol = quote.get("symbol")
            bid = quote.get("bid")
            ask = quote.get("ask")
            if not isinstance(symbol, str) or not symbol:
                continue
            if not _numeric(bid) or not _numeric(ask):
                continue
            await self._service.ingest_event(
                self._build_event(quote, symbol, str(bid), str(ask), sequence)
            )

    def _build_event(
        self,
        quote: dict[str, Any],
        symbol: str,
        bid: str,
        ask: str,
        sequence: object,
    ) -> MarketEvent:
        """Build one normalized quote event from a snapshot quote.

        Args:
            quote: Raw snapshot quote mapping.
            symbol: Validated symbol name.
            bid: Validated bid rendered as a string.
            ask: Validated ask rendered as a string.
            sequence: Snapshot frame sequence when integral.

        Returns:
            Fully formed MarketEvent ready for ingestion.
        """
        values: dict[str, Any] = {"symbol": symbol, "bid": bid, "ask": ask}
        for optional in ("last", "volume", "digits", "spread"):
            optional_value = quote.get(optional)
            if optional_value is not None:
                values[optional] = optional_value
        digest = hashlib.sha256(
            json.dumps(
                {key: values[key] for key in sorted(values)},
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        event_time = _ms_to_timestamp(quote.get("time_msc"))
        sequence_int: int | None = sequence if _is_int(sequence) else None
        return MarketEvent(
            event_id=str(uuid.uuid7()),
            provider=self._provider,
            event_kind="QUOTE",
            event_time=event_time or _utc_now_timestamp(),
            receipt_time=_utc_now_timestamp(),
            provider_sequence=sequence_int,
            ordering_mode="PROVIDER_SEQUENCE"
            if sequence_int is not None
            else "RECEIPT_ORDER",
            instrument=None,
            values=values,
            raw_hash=digest,
        )
