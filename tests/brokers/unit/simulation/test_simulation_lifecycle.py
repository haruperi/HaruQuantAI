"""Lifecycle tests for FEAT-BRK-17."""

import asyncio
from typing import Any

from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    finalize_simulation_broker_session,
)


class _Authority:
    """Delegate the structural port to the canonical deterministic fake."""

    def __init__(self, target: object) -> None:
        self._target = target

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    async def finalize_session(self) -> object:
        """Finalize by disconnecting the deterministic target."""
        return await self._target.disconnect()  # type: ignore[attr-defined, no-any-return]

    async def ping(self) -> object:
        """Return a canonical successful local probe response."""
        return await self._target.is_connected()  # type: ignore[attr-defined, no-any-return]


def _adapter() -> object:
    config = build_broker_connection_config("sim", "simulation")
    fake = create_configured_fake_broker_adapter(config)
    response = create_simulation_broker_adapter(config, _Authority(fake))
    assert response.status == "success"
    assert response.data is not None
    return response.data


def test_connect_disconnect_reconnect_ping_status_and_finalize() -> None:
    """The adapter mirrors the complete admitted lifecycle."""

    async def exercise() -> None:
        adapter = _adapter()
        assert (await adapter.connect()).status == "success"  # type: ignore[attr-defined]
        assert (await adapter.ping()).status == "success"  # type: ignore[attr-defined]
        assert (await adapter.is_connected()).data is True  # type: ignore[attr-defined]
        assert (await adapter.get_connection_status()).data.state == "ready"  # type: ignore[attr-defined, union-attr]
        assert (await adapter.disconnect()).status == "success"  # type: ignore[attr-defined]
        assert (await adapter.disconnect()).status == "success"  # type: ignore[attr-defined]
        assert (await adapter.reconnect()).status == "success"  # type: ignore[attr-defined]
        assert (await finalize_simulation_broker_session(adapter)).status == "success"

    asyncio.run(exercise())


def test_ping_is_blocked_while_disconnected() -> None:
    """Session-required behavior fails closed before delegation."""

    async def exercise() -> None:
        response = await _adapter().ping()  # type: ignore[attr-defined]
        assert response.status == "error"
        assert response.error.code == "BROKER_NOT_CONNECTED"

    asyncio.run(exercise())
