"""Contract and conformance tests for data.tick_stream.v1 capability."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from app.contracts.data.tick_stream.v1 import (
    CAPABILITY_ID,
    TickStreamCapabilityV1,
    TickStreamEventV1,
    TickStreamRequestV1,
)

from tests.removability.harness import run_in_fresh_process


def test_capability_id_and_exports() -> None:
    """Verify capability ID matches specification."""
    assert CAPABILITY_ID == "data.tick_stream.v1"


def test_request_validation() -> None:
    """Verify request bounds validation."""
    with pytest.raises(ValueError, match="symbol must be a non-blank string"):
        TickStreamRequestV1(symbol="")

    with pytest.raises(ValueError, match="symbol must be a non-blank string"):
        TickStreamRequestV1(symbol="   ")

    with pytest.raises(ValueError, match="buffer_size must be between 1 and 4096"):
        TickStreamRequestV1(symbol="EURUSD", buffer_size=0)

    with pytest.raises(ValueError, match="buffer_size must be between 1 and 4096"):
        TickStreamRequestV1(symbol="EURUSD", buffer_size=5000)

    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=512)
    assert req.symbol == "EURUSD"
    assert req.buffer_size == 512


def test_event_validation() -> None:
    """Verify event bounds and immutable payload validation."""
    with pytest.raises(ValueError, match="sequence must be >= 1"):
        TickStreamEventV1(sequence=0, symbol="EURUSD", payload={"bid": 1.05})

    with pytest.raises(ValueError, match="symbol must be a non-blank string"):
        TickStreamEventV1(sequence=1, symbol="", payload={"bid": 1.05})

    event = TickStreamEventV1(sequence=1, symbol="EURUSD", payload={"bid": 1.05})
    assert event.sequence == 1
    assert event.symbol == "EURUSD"
    assert event.payload["bid"] == 1.05


class _FakeTickStream:
    """Deterministic fake provider conforming to TickStreamCapabilityV1."""

    def __init__(self) -> None:
        self._active = False
        self._generation_id: str | None = None
        self._queue: asyncio.Queue[TickStreamEventV1] = asyncio.Queue()

    @property
    def active(self) -> bool:
        return self._active

    @property
    def generation_id(self) -> str | None:
        return self._generation_id

    async def start(self, request: TickStreamRequestV1) -> None:
        self._active = True
        self._generation_id = "gen-1"
        for i in range(1, 4):
            event = TickStreamEventV1(
                sequence=i,
                symbol=request.symbol,
                payload={"bid": 1.05 + i * 0.001, "ask": 1.051 + i * 0.001},
            )
            await self._queue.put(event)

    async def events(self) -> AsyncIterator[TickStreamEventV1]:
        while self._active or not self._queue.empty():
            try:
                yield await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except TimeoutError:
                break

    async def stop(self) -> None:
        self._active = False
        self._generation_id = None


@pytest.mark.anyio
async def test_fake_stream_conformance() -> None:
    """Verify fake implementation conforms to TickStreamCapabilityV1 protocol."""
    provider = _FakeTickStream()
    assert isinstance(provider, TickStreamCapabilityV1)
    assert provider.active is False
    assert provider.generation_id is None

    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=100)
    await provider.start(req)
    assert provider.active is True
    assert provider.generation_id == "gen-1"

    collected: list[TickStreamEventV1] = []
    async for ev in provider.events():
        collected.append(ev)

    assert len(collected) == 3
    assert [ev.sequence for ev in collected] == [1, 2, 3]

    await provider.stop()
    assert provider.active is False
    assert provider.generation_id is None


def test_import_isolation() -> None:
    """Verify capability contract can be loaded without importing business domains."""
    script = """
import sys
import app.contracts.data.tick_stream.v1 as cap

for name, mod in list(sys.modules.items()):
    if mod is None:
        continue
    assert not (name.startswith("app.services") or name.startswith("app.agentic")), f"Found domain import: {name}"
"""
    repo_root = Path(__file__).resolve().parents[3]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr
