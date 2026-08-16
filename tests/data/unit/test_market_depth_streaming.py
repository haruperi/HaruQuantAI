"""Unit evidence for Data-owned multi-symbol MT5 Depth-of-Market reads."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal

from app.services.data import (
    build_market_depth_stream_request,
    stream_market_depth,
)
from app.services.data.market_events import mt5_depth
from app.utils import generate_id


def test_depth_stream_filters_atomically_without_synthesizing_missing_levels(
    monkeypatch,
) -> None:
    """One upstream book frame yields only requested symbols and real levels."""

    async def source() -> AsyncGenerator[dict[str, object]]:
        now = datetime.now(UTC)
        yield {
            "sequence": 2,
            "received_at": now,
            "source_id": "mt5-terminal-1",
            "gap": 0,
            "errors": ({"symbol": "USDJPY", "code": 0},),
            "books": (
                {
                    "symbol": "EURUSD",
                    "book_depth": 10,
                    "bids": ({"price": Decimal("1.1000"), "volume": Decimal("2.5")},),
                    "asks": ({"price": Decimal("1.1002"), "volume": Decimal("1.0")},),
                },
                {
                    "symbol": "GBPUSD",
                    "book_depth": 10,
                    "bids": (),
                    "asks": (),
                },
            ),
        }

    async def scenario() -> None:
        released: list[str] = []

        async def acquire(_symbols: tuple[str, ...]) -> str:
            return "consumer-test"

        async def release(consumer_id: str) -> None:
            released.append(consumer_id)

        monkeypatch.setattr(mt5_depth, "stream_metatrader_book_snapshots", source)
        monkeypatch.setattr(mt5_depth, "acquire_metatrader_snapshot_symbols", acquire)
        monkeypatch.setattr(mt5_depth, "release_metatrader_snapshot_symbols", release)
        request = build_market_depth_stream_request(
            symbols=("EURUSD", "USDJPY"),
            request_id=generate_id("req"),
        )
        stream = stream_market_depth(request)
        event = await anext(stream)
        await stream.aclose()

        assert event.sequence == 2
        assert len(event.books) == 1
        assert event.books[0]["symbol"] == "EURUSD"
        assert event.books[0]["bids"][0]["price"] == Decimal("1.1000")
        assert len(event.errors) == 1
        assert event.errors[0]["symbol"] == "USDJPY"
        assert released == ["consumer-test"]

    asyncio.run(scenario())


def test_depth_stream_skips_a_frame_with_nothing_for_requested_symbols(
    monkeypatch,
) -> None:
    """A frame covering only unrequested symbols yields nothing, not an empty event."""

    async def source() -> AsyncGenerator[dict[str, object]]:
        now = datetime.now(UTC)
        yield {
            "sequence": 1,
            "received_at": now,
            "source_id": "mt5-terminal-1",
            "gap": 0,
            "errors": (),
            "books": ({"symbol": "GBPUSD", "book_depth": 10, "bids": (), "asks": ()},),
        }
        yield {
            "sequence": 2,
            "received_at": now,
            "source_id": "mt5-terminal-1",
            "gap": 0,
            "errors": (),
            "books": ({"symbol": "EURUSD", "book_depth": 10, "bids": (), "asks": ()},),
        }

    async def scenario() -> None:
        async def acquire(_symbols: tuple[str, ...]) -> str:
            return "consumer-test"

        async def release(_consumer_id: str) -> None:
            return None

        monkeypatch.setattr(mt5_depth, "stream_metatrader_book_snapshots", source)
        monkeypatch.setattr(mt5_depth, "acquire_metatrader_snapshot_symbols", acquire)
        monkeypatch.setattr(mt5_depth, "release_metatrader_snapshot_symbols", release)
        request = build_market_depth_stream_request(
            symbols=("EURUSD",),
            request_id=generate_id("req"),
        )
        stream = stream_market_depth(request)
        event = await anext(stream)
        await stream.aclose()

        assert event.sequence == 2
        assert event.books[0]["symbol"] == "EURUSD"

    asyncio.run(scenario())
