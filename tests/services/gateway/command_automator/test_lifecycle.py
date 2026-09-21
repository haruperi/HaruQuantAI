"""Lifecycle tests for gateway command automator feature."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
import uvicorn
from app.contracts.gateway import GATEWAY_AUTOMATION
from app.contracts.workspace import WORKSPACE_DIAGNOSTICS
from app.kernel.bootstrapper import Runtime
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.services.gateway.application import ApplicationFeature
from app.services.gateway.command_automator import CommandAutomationFeature


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


def test_command_automator_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test standard feature composition lifecycle for command automator."""

    async def _mock_serve(self: uvicorn.Server) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(uvicorn.Server, "serve", _mock_serve)

    async def _test() -> None:
        async with Runtime(
            (
                DummyDiagnosticsFeature,
                ApplicationFeature,
                CommandAutomationFeature,
            )
        ) as runtime:
            automator = runtime.require(GATEWAY_AUTOMATION)
            res = await automator.execute_command("-status")
            assert res.success is True

    asyncio.run(_test())
