"""Lifecycle tests for gateway streams feature."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
import uvicorn
from app.contracts.gateway import GATEWAY_STREAMS
from app.contracts.workspace import WORKSPACE_DIAGNOSTICS
from app.kernel.bootstrapper import Runtime
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.services.gateway.application import ApplicationFeature
from app.services.gateway.streams import StreamsFeature


class DummyDiagnosticsFeature:
    """Mock diagnostics provider."""

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            name="test.diagnostics",
            provides=frozenset({WORKSPACE_DIAGNOSTICS}),
            requires=frozenset(),
            description="Dummy diagnostics.",
        )

    async def start(self, context: FeatureContext) -> None:
        context.provide(WORKSPACE_DIAGNOSTICS, cast("Any", object()))

    async def stop(self) -> None:
        pass


def test_streams_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test standard feature composition lifecycle for streams."""

    async def _mock_serve(self: uvicorn.Server) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(uvicorn.Server, "serve", _mock_serve)

    async def _test() -> None:
        async with Runtime(
            (DummyDiagnosticsFeature, ApplicationFeature, StreamsFeature)
        ) as runtime:
            streams = runtime.require(GATEWAY_STREAMS)
            assert streams.get_active_connections_count() == 0

    asyncio.run(_test())
