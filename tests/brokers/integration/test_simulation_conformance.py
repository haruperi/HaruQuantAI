"""Canonical conformance tests for FEAT-BRK-17."""

import asyncio
from typing import Any

from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    run_broker_adapter_conformance,
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


def test_simulation_adapter_passes_admitted_intersection() -> None:
    """Simulation retains the canonical schema and fail-closed surface."""

    async def exercise() -> None:
        config = build_broker_connection_config("sim", "simulation")
        authority = _Authority(create_configured_fake_broker_adapter(config))
        adapter = create_simulation_broker_adapter(config, authority).data
        assert adapter is not None
        verdict = await run_broker_adapter_conformance(
            adapter=adapter,
            broker_id="sim",
            environment="simulation",
            unsupported_capability_id="refresh_session",
            unsupported_operation="refresh_session",
        )
        assert verdict["aggregate_verdict"] == "PASSED"

    asyncio.run(exercise())
