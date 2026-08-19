"""Unit evidence for Data-owned multi-symbol MT5 snapshots."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal

import app.services.brokers as brokers_root
from app.services.data import (
    build_market_snapshot_stream_request,
    stream_market_snapshots,
)
from app.utils import generate_id


def test_snapshot_stream_filters_atomically_and_calculates_spread(
    monkeypatch,
) -> None:
    """One upstream frame yields only requested symbols without polling MT5."""

    async def source() -> AsyncGenerator[dict[str, object]]:
        now = datetime.now(UTC)
        yield {
            "sequence": 4,
            "received_at": now,
            "source_id": "mt5-terminal-1",
            "errors": (),
            "quotes": (
                {
                    "symbol": "EURUSD",
                    "time_msc": int(now.timestamp() * 1_000),
                    "bid": Decimal("1.1000"),
                    "ask": Decimal("1.1002"),
                    "last": None,
                    "volume": 1,
                    "volume_real": Decimal(1),
                    "flags": 6,
                    "digits": 5,
                },
                {
                    "symbol": "GBPUSD",
                    "time_msc": int(now.timestamp() * 1_000),
                    "bid": Decimal("1.2000"),
                    "ask": Decimal("1.2003"),
                    "last": None,
                    "volume": 2,
                    "volume_real": Decimal(2),
                    "flags": 6,
                    "digits": 5,
                },
            ),
        }

    async def scenario() -> None:
        released: list[str] = []

        async def acquire(_symbols: tuple[str, ...]) -> str:
            return "consumer-test"

        async def release(consumer_id: str) -> None:
            released.append(consumer_id)

        monkeypatch.setattr(brokers_root, "stream_metatrader_snapshots", source)
        monkeypatch.setattr(
            brokers_root, "acquire_metatrader_snapshot_symbols", acquire
        )
        monkeypatch.setattr(
            brokers_root, "release_metatrader_snapshot_symbols", release
        )
        request = build_market_snapshot_stream_request(
            symbols=("GBPUSD",),
            request_id=generate_id("req"),
        )
        stream = stream_market_snapshots(request)
        event = await anext(stream)
        await stream.aclose()
        assert event.sequence == 4
        assert len(event.quotes) == 1
        assert event.quotes[0]["symbol"] == "GBPUSD"
        assert event.quotes[0]["spread"] == Decimal("0.0003")
        assert released == ["consumer-test"]

    asyncio.run(scenario())
