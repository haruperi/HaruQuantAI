"""Standalone usage evidence for FEAT-BRK-17 simulation channel."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    finalize_simulation_broker_session,
    get_broker_capability_catalogue,
    get_broker_environment,
    get_broker_id,
)


class _UsageAuthority:
    """In-memory authority satisfying the Brokers-owned structural port."""

    def __init__(self, target: object) -> None:
        self._target = target

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    async def ping(self) -> object:
        """Return a successful canonical local probe."""
        return await self._target.is_connected()  # type: ignore[attr-defined, no-any-return]

    async def finalize_session(self) -> object:
        """Finalize without any external side effect."""
        return await self._target.disconnect()  # type: ignore[attr-defined, no-any-return]


def _values() -> tuple[object, object, object]:
    config = build_broker_connection_config("sim", "simulation")
    authority = _UsageAuthority(create_configured_fake_broker_adapter(config))
    adapter = create_simulation_broker_adapter(config, authority).data
    assert adapter is not None
    return config, authority, adapter


def fr_brk_167() -> None:
    """Demonstrate the exact simulation identity and environment."""
    assert str(get_broker_id("sim")) == "sim"
    assert str(get_broker_environment("simulation")) == "simulation"


def fr_brk_168() -> None:
    """Demonstrate exact factory construction."""
    assert _values()[2] is not None


def fr_brk_169() -> None:
    """Demonstrate the published capability intersection."""
    catalogue = get_broker_capability_catalogue().data
    assert catalogue is not None
    assert catalogue[get_broker_id("sim")]


async def fr_brk_170() -> None:
    """Demonstrate authority-backed lifecycle and finalization."""
    adapter = _values()[2]
    assert (await adapter.connect()).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.ping()).status == "success"  # type: ignore[attr-defined]
    assert (await adapter.reconnect()).status == "success"  # type: ignore[attr-defined]
    assert (await finalize_simulation_broker_session(adapter)).status == "success"


def fr_brk_171() -> None:
    """Demonstrate credential- and endpoint-free isolation."""
    config = _values()[0]
    assert config.credentials is None  # type: ignore[attr-defined]
    assert config.endpoint is None  # type: ignore[attr-defined]


def fr_brk_172() -> None:
    """Demonstrate structural authority injection."""
    assert isinstance(_values()[1], _UsageAuthority)


async def _run() -> None:
    fr_brk_167()
    fr_brk_168()
    fr_brk_169()
    await fr_brk_170()
    fr_brk_171()
    fr_brk_172()


def main() -> None:
    """Execute all requirement evidence."""
    asyncio.run(_run())
    print("FEAT-BRK-17 simulation usage: SUCCESS")


if __name__ == "__main__":
    main()
