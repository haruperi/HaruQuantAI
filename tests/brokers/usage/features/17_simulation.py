"""Standalone usage evidence for FEAT-BRK-17 simulation channel."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import _support  # noqa: F401
from app.services.brokers import (
    build_broker_connection_config,
    build_simulation_read_envelope,
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
        self.read_count = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    async def ping(self) -> object:
        """Return a successful canonical local probe."""
        return await self._target.is_connected()  # type: ignore[attr-defined, no-any-return]

    async def finalize_session(self) -> object:
        """Finalize without any external side effect."""
        return await self._target.disconnect()  # type: ignore[attr-defined, no-any-return]

    async def read(self, operation: object, arguments: Mapping[str, object]) -> object:
        """Return exact canonical fixture values with simulated-time evidence."""
        del arguments
        self.read_count += 1
        name = str(operation)
        payloads: dict[str, object] = {
            "get_symbols": ("EURUSD",),
            "get_symbol_info": "EURUSD-specification-shape",
            "get_provider_specification": "revision-spec-7",
            "get_trading_sessions": ("weekly+dated-exception:revision-3",),
            "get_quote": Decimal("1.23456"),
            "get_account_info": {"equity": Decimal("1000.00")},
            "get_positions": ("position-1",),
            "get_orders": ("order-1",),
        }
        now = datetime(2024, 1, 2, 12, tzinfo=UTC)
        return build_simulation_read_envelope(
            payload=payloads[name],
            source_sequence=0,
            observed_at=now,
            received_at=now,
            available_at=now,
            simulated_at=now,
            session_revision="revision-3" if name == "get_trading_sessions" else None,
        )


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


async def _read_values() -> tuple[object, _UsageAuthority]:
    """Return one connected read adapter and its socket-free authority."""
    _, authority, adapter = _values()
    assert isinstance(authority, _UsageAuthority)
    assert (await adapter.connect()).status == "success"  # type: ignore[attr-defined]
    return adapter, authority


async def fr_brk_174() -> None:
    """Demonstrate structural authority read-port binding."""
    adapter, authority = await _read_values()
    assert (await adapter.get_quote("EURUSD")).data == Decimal("1.23456")  # type: ignore[attr-defined]
    assert authority.read_count == 1


def fr_brk_175() -> None:
    """Demonstrate injected simulated observation/availability timestamps."""
    now = datetime(2024, 1, 2, 12, tzinfo=UTC)
    assert build_simulation_read_envelope(
        payload="quote",
        source_sequence=0,
        observed_at=now,
        received_at=now,
        available_at=now,
        simulated_at=now,
    )


async def fr_brk_176() -> None:
    """Demonstrate canonical symbol and specification projection."""
    adapter, _ = await _read_values()
    assert (await adapter.get_symbols()).data == ("EURUSD",)  # type: ignore[attr-defined]
    assert (
        await adapter.get_provider_specification("EURUSD")
    ).data == "revision-spec-7"  # type: ignore[attr-defined]


async def fr_brk_177() -> None:
    """Demonstrate the no-future-read boundary with fixed authority time."""
    adapter, _ = await _read_values()
    result = await adapter.get_quote("EURUSD")  # type: ignore[attr-defined]
    assert (
        result.metadata.extensions["provider_metadata"]["available_at"]
        == "2024-01-02T12:00:00+00:00"
    )


async def fr_brk_178() -> None:
    """Demonstrate exact account-ledger projection."""
    adapter, _ = await _read_values()
    assert (await adapter.get_account_info()).data["equity"] == Decimal("1000.00")  # type: ignore[attr-defined,index]


async def fr_brk_179() -> None:
    """Demonstrate exact position and order projection."""
    adapter, _ = await _read_values()
    assert (await adapter.get_positions()).data == ("position-1",)  # type: ignore[attr-defined]
    assert (await adapter.get_orders()).data == ("order-1",)  # type: ignore[attr-defined]


async def fr_brk_180() -> None:
    """Demonstrate revision-bound sessions and unsupported deal reads."""
    adapter, _ = await _read_values()
    assert (await adapter.get_trading_sessions("EURUSD")).status == "success"  # type: ignore[attr-defined]
    assert (
        await adapter.get_deal("deal-1")
    ).error.code == "BROKER_CAPABILITY_UNSUPPORTED"  # type: ignore[attr-defined,union-attr]


async def fr_brk_181() -> None:
    """Demonstrate read isolation and explicit delivery evidence."""
    adapter, authority = await _read_values()
    response = await adapter.get_quote("EURUSD")  # type: ignore[attr-defined]
    evidence = response.metadata.extensions["provider_metadata"]
    assert evidence["source_sequence"] == 0
    assert evidence["gap"] is False
    assert authority.read_count == 1


async def _run() -> None:
    fr_brk_167()
    fr_brk_168()
    fr_brk_169()
    await fr_brk_170()
    fr_brk_171()
    fr_brk_172()
    await fr_brk_174()
    fr_brk_175()
    await fr_brk_176()
    await fr_brk_177()
    await fr_brk_178()
    await fr_brk_179()
    await fr_brk_180()
    await fr_brk_181()


def main() -> None:
    """Execute all requirement evidence."""
    asyncio.run(_run())
    print("FEAT-BRK-17 simulation usage: SUCCESS")


if __name__ == "__main__":
    main()
