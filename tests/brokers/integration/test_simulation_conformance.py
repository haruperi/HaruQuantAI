"""Canonical conformance tests for FEAT-BRK-17."""

import asyncio
from typing import Any

from app.services.brokers import (
    build_broker_connection_config,
    create_configured_fake_broker_adapter,
    create_simulation_broker_adapter,
    get_broker_capability_catalogue,
    get_broker_capability_id,
    get_broker_id,
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


def test_simulation_adapter_passes_canonical_conformance() -> None:
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
            unsupported_capability_id="get_deal",
            unsupported_operation="get_deal",
        )
        assert verdict["aggregate_verdict"] == "PASSED"

    asyncio.run(exercise())


def test_simulation_capability_manifest_is_exhaustive_and_bounded() -> None:
    """The manifest declares the clock-safe read intersection exactly."""
    catalogue = get_broker_capability_catalogue().data
    assert catalogue is not None
    capabilities = catalogue[get_broker_id("sim")]
    assert len(capabilities) == len(
        tuple(type(item.capability) for item in capabilities)
    )
    ping = next(
        item
        for item in capabilities
        if item.capability == get_broker_capability_id("ping")
    )
    quote = next(
        item
        for item in capabilities
        if item.capability == get_broker_capability_id("get_quote")
    )
    unsupported = next(
        item
        for item in capabilities
        if item.capability == get_broker_capability_id("get_deal")
    )
    assert ping.availability == "AVAILABLE"
    assert quote.availability == "AVAILABLE"
    assert unsupported.availability == "UNAVAILABLE"
