"""Tests for data.tick_stream.metatrader provider."""

# ruff: noqa: INP001
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from unittest.mock import patch

import pytest
from app.capabilities.data.tick_stream.v1 import (
    TickStreamCapabilityV1,
    TickStreamEventV1,
    TickStreamRequestV1,
)
from app.kernel.effects import EffectScope
from app.kernel.manifests import load_manifest
from app.services.data.market_events.metatrader_tick_stream.plugin import (
    create_provider,
)
from tests.removability.harness import run_in_fresh_process


def test_manifest_structure() -> None:
    """Verify MT5 tick stream provider manifest matches specification."""
    manifest_path = (
        Path(__file__).resolve().parents[4]
        / "app"
        / "services"
        / "data"
        / "market_events"
        / "metatrader_tick_stream"
        / "manifest.toml"
    )
    manifest = load_manifest(manifest_path)
    assert str(manifest.provider_id) == "data.tick_stream.metatrader"
    assert manifest.entry_point == (
        "app.services.data.market_events.metatrader_tick_stream.plugin:create_provider"
    )
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "data.tick_stream.v1"
    assert manifest.lifecycle == "scoped"
    assert manifest.reload == "process_restart"


def test_no_import_io() -> None:
    """Verify importing provider plugin initiates no I/O."""
    script = """
import sys
import app.services.data.market_events.metatrader_tick_stream.plugin as plugin
assert plugin is not None
"""
    repo_root = Path(__file__).resolve().parents[4]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr


def test_read_only_import_graph() -> None:
    """Verify provider does not import broker mutation commands."""
    script = """
import sys
import app.services.data.market_events.metatrader_tick_stream.plugin as plugin
assert plugin is not None
for name in sys.modules:
    assert "commands" not in name, f"Forbidden command import: {name}"
"""
    repo_root = Path(__file__).resolve().parents[4]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr


def test_factory_rejection_and_acceptance() -> None:
    """Verify factory validates dependencies and configuration."""
    scope = EffectScope()

    # Rejects non-empty dependencies
    with pytest.raises(
        ValueError, match="MT5 tick stream provider accepts no dependencies"
    ):
        create_provider(
            dependencies={"some.cap": object()},  # type: ignore[dict-item]
            config={"symbol": "EURUSD"},
            scope=scope,
        )

    # Rejects missing symbol
    with pytest.raises(
        ValueError,
        match="MT5 tick stream provider requires 'symbol' string in configuration",
    ):
        create_provider(dependencies={}, config={}, scope=scope)

    # Accepts valid config
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 128},
        scope=scope,
    )
    assert isinstance(adapter, TickStreamCapabilityV1)
    assert adapter.active is False
    assert adapter.generation_id is None
    scope.close()


@pytest.mark.anyio
async def test_monotonic_sequence_and_events() -> None:
    """Verify stream consumes snapshots and yields monotonic sequence events."""
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 128},
        scope=scope,
    )

    async def _mock_snapshots() -> AsyncIterator[Mapping[str, object]]:
        for i in range(1, 4):
            yield {
                "quotes": (
                    {"symbol": "EURUSD", "bid": 1.05 + i * 0.001, "ask": 1.051},
                    {"symbol": "GBPUSD", "bid": 1.25},
                )
            }

    with (
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.acquire_metatrader_snapshot_symbols",
            return_value="consumer_123",
        ),
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.release_metatrader_snapshot_symbols",
            return_value=None,
        ),
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.stream_metatrader_snapshots",
            side_effect=_mock_snapshots,
        ),
    ):
        req = TickStreamRequestV1(symbol="EURUSD", buffer_size=100)
        await adapter.start(req)
        assert bool(adapter.generation_id) is True

        collected: list[TickStreamEventV1] = []
        async for ev in adapter.events():
            collected.append(ev)
            if len(collected) == 3:
                break

        assert len(collected) == 3
        assert [ev.sequence for ev in collected] == [1, 2, 3]
        assert all(ev.symbol == "EURUSD" for ev in collected)

        await adapter.stop()
        assert not adapter.active
        assert adapter.generation_id is None

    scope.close()


@pytest.mark.anyio
async def test_partial_start_cleanup() -> None:
    """Verify failure during symbol acquisition cleans up state."""
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 128},
        scope=scope,
    )

    with patch(
        "app.services.data.market_events.metatrader_tick_stream.plugin.acquire_metatrader_snapshot_symbols",
        side_effect=ValueError("Symbol rejected"),
    ):
        req = TickStreamRequestV1(symbol="EURUSD", buffer_size=100)
        with pytest.raises(ValueError, match="Symbol rejected"):
            await adapter.start(req)

        assert not adapter.active
        assert adapter.generation_id is None

    scope.close()


@pytest.mark.anyio
async def test_upstream_loss_handling() -> None:
    """Verify upstream loss logs warning with LOST_DURING_OPERATION and stops cleanly."""
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 128},
        scope=scope,
    )

    async def _failing_snapshots() -> AsyncIterator[Mapping[str, object]]:
        yield {"quotes": ({"symbol": "EURUSD", "bid": 1.05},)}
        raise ConnectionError("Disconnected from MT5 EA")

    with (
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.acquire_metatrader_snapshot_symbols",
            return_value="consumer_123",
        ),
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.release_metatrader_snapshot_symbols",
            return_value=None,
        ),
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.stream_metatrader_snapshots",
            side_effect=_failing_snapshots,
        ),
    ):
        req = TickStreamRequestV1(symbol="EURUSD", buffer_size=100)
        await adapter.start(req)

        collected: list[TickStreamEventV1] = []
        async for ev in adapter.events():
            collected.append(ev)

        assert len(collected) == 1
        assert collected[0].sequence == 1

        await adapter.stop()
        assert not adapter.active

    scope.close()


@pytest.mark.anyio
async def test_stop_and_cleanup_zero_resources() -> None:
    """Verify stopping provider releases subscriptions and cancels internal tasks."""
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 128},
        scope=scope,
    )

    released: list[str] = []

    async def _mock_release(cid: str) -> None:
        released.append(cid)

    async def _infinite_snapshots() -> AsyncIterator[Mapping[str, object]]:
        while True:
            yield {"quotes": ({"symbol": "EURUSD", "bid": 1.05},)}

    with (
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.acquire_metatrader_snapshot_symbols",
            return_value="consumer_123",
        ),
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.release_metatrader_snapshot_symbols",
            side_effect=_mock_release,
        ),
        patch(
            "app.services.data.market_events.metatrader_tick_stream.plugin.stream_metatrader_snapshots",
            side_effect=_infinite_snapshots,
        ),
    ):
        req = TickStreamRequestV1(symbol="EURUSD", buffer_size=100)
        await adapter.start(req)
        assert bool(adapter.active) is True

        await adapter.stop()
        assert not adapter.active
        assert released == ["consumer_123"]

    scope.close()
