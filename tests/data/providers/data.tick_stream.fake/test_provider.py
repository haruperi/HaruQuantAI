"""Tests for data.tick_stream.fake provider."""

# ruff: noqa: INP001
from pathlib import Path

import pytest
from app.contracts.data.tick_stream.v1 import (
    TickStreamCapabilityV1,
    TickStreamEventV1,
    TickStreamRequestV1,
)
from app.kernel.effects import EffectScope
from app.kernel.manifests import load_manifest
from app.services.data.market_events.fake_tick_stream.plugin import (
    create_provider,
)
from tests.removability.harness import run_in_fresh_process


def test_manifest_structure() -> None:
    """Verify fake tick stream provider manifest matches specification."""
    manifest_path = (
        Path(__file__).resolve().parents[4]
        / "app"
        / "services"
        / "data"
        / "market_events"
        / "fake_tick_stream"
        / "manifest.toml"
    )
    manifest = load_manifest(manifest_path)
    assert str(manifest.provider_id) == "data.tick_stream.fake"
    assert manifest.entry_point == (
        "app.services.data.market_events.fake_tick_stream.plugin:create_provider"
    )
    assert len(manifest.provides) == 1
    assert str(manifest.provides[0].capability_id) == "data.tick_stream.v1"
    assert manifest.lifecycle == "scoped"
    assert manifest.reload == "config_restart"


def test_no_import_io() -> None:
    """Verify importing provider plugin initiates no I/O."""
    script = """
import sys
import app.services.data.market_events.fake_tick_stream.plugin as plugin
assert plugin is not None
"""
    repo_root = Path(__file__).resolve().parents[4]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr


def test_factory_rejection_and_acceptance() -> None:
    """Verify factory validates dependencies and configuration."""
    scope = EffectScope()

    # Rejection: invalid config
    with pytest.raises(
        ValueError,
        match="fake tick stream config must be symbol EURUSD and buffer_size 3",
    ):
        create_provider(
            dependencies={},
            config={"symbol": "GBPUSD", "buffer_size": 3},
            scope=scope,
        )

    with pytest.raises(
        ValueError,
        match="fake tick stream config must be symbol EURUSD and buffer_size 3",
    ):
        create_provider(
            dependencies={},
            config={"symbol": "EURUSD", "buffer_size": 10},
            scope=scope,
        )

    # Acceptance: valid config
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 3},
        scope=scope,
    )
    assert isinstance(adapter, TickStreamCapabilityV1)
    assert adapter.active is False
    assert adapter.generation_id is None
    scope.close()


@pytest.mark.anyio
async def test_exact_three_events() -> None:
    """Verify fake stream yields exactly three known events."""
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 3},
        scope=scope,
    )

    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=3)
    await adapter.start(req)
    assert bool(adapter.active) is True
    assert bool(adapter.generation_id) is True

    collected: list[TickStreamEventV1] = []
    async for ev in adapter.events():
        collected.append(ev)

    assert len(collected) == 3
    assert [ev.sequence for ev in collected] == [1, 2, 3]
    assert [ev.payload.get("bid") for ev in collected] == [
        "1.1000",
        "1.1001",
        "1.1002",
    ]

    await adapter.stop()
    assert not adapter.active
    scope.close()


@pytest.mark.anyio
async def test_stop_twice_idempotency() -> None:
    """Verify stopping adapter multiple times is idempotent."""
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 3},
        scope=scope,
    )

    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=3)
    await adapter.start(req)
    await adapter.stop()
    assert not adapter.active
    await adapter.stop()
    assert not adapter.active
    scope.close()


@pytest.mark.anyio
async def test_new_generation_and_unique_identities() -> None:
    """Verify each start generates a new generation ID and unique event pairs."""
    scope = EffectScope()
    adapter = create_provider(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 3},
        scope=scope,
    )

    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=3)
    await adapter.start(req)
    gen1 = adapter.generation_id

    events1: list[tuple[str | None, int]] = []
    async for ev in adapter.events():
        events1.append((gen1, ev.sequence))

    await adapter.stop()

    await adapter.start(req)
    gen2 = adapter.generation_id

    events2: list[tuple[str | None, int]] = []
    async for ev in adapter.events():
        events2.append((gen2, ev.sequence))

    await adapter.stop()

    assert gen1 is not None
    assert gen2 is not None
    assert gen1 != gen2

    all_identities = set(events1 + events2)
    assert len(all_identities) == 6
    scope.close()
