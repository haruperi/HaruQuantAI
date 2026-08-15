"""Exact factory-selection tests for FEAT-BRK-17."""

from typing import Any

import pytest
from app.services.brokers import (
    build_broker_connection_config,
    create_broker_adapter,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    get_broker_id,
)


class _Authority:
    def __init__(self, target: object) -> None:
        self._target = target

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)

    async def finalize_session(self) -> object:
        return await self._target.disconnect()  # type: ignore[attr-defined, no-any-return]

    async def ping(self) -> object:
        return await self._target.is_connected()  # type: ignore[attr-defined, no-any-return]


def test_factory_registers_only_exact_simulation_pair() -> None:
    """Only sim plus simulation plus an authority creates the adapter."""
    config = build_broker_connection_config("sim", "simulation")
    authority = _Authority(create_configured_fake_broker_adapter(config))
    assert create_simulation_broker_adapter(config, authority).status == "success"
    assert create_broker_adapter(get_broker_id("sim"), config).status == "error"


@pytest.mark.parametrize("environment", ["live", "demo", "testnet", "sandbox"])
def test_factory_rejects_sim_with_non_simulation_environment(environment: str) -> None:
    """No live-like environment aliases the in-process channel."""
    config = build_broker_connection_config("sim", environment)
    authority = _Authority(create_configured_fake_broker_adapter(config))
    assert create_simulation_broker_adapter(config, authority).status == "error"


def test_factory_rejects_simulation_environment_for_real_provider() -> None:
    """Simulation cannot be injected into a real provider registration."""
    config = build_broker_connection_config("yahoo", "simulation")
    result = create_broker_adapter(get_broker_id("yahoo"), config, object())
    assert result.status == "error"
