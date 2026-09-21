"""Lifecycle and composition tests for gateway application."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import pytest
import uvicorn
from app.contracts.gateway import GATEWAY_APPLICATION, HTTP_SERVER
from app.contracts.workspace import WORKSPACE_DIAGNOSTICS
from app.kernel.bootstrapper import Runtime
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.services.gateway.application import (
    ApplicationConfig,
    ApplicationFeature,
)


class DummyDiagnostics:
    """Mock diagnostics service for testing."""

    def get_system_info(self) -> None:
        return None


class DummyDiagnosticsFeature:
    """Feature providing dummy WORKSPACE_DIAGNOSTICS."""

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            name="test.diagnostics",
            provides=frozenset({WORKSPACE_DIAGNOSTICS}),
            requires=frozenset(),
            description="Dummy diagnostics for gateway testing.",
        )

    async def start(self, context: FeatureContext) -> None:
        context.provide(WORKSPACE_DIAGNOSTICS, cast("Any", DummyDiagnostics()))

    async def stop(self) -> None:
        pass


def test_application_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify application startup, capability provision, and graceful shutdown."""

    async def _mock_serve(self: uvicorn.Server) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(uvicorn.Server, "serve", _mock_serve)

    def diag_factory() -> DummyDiagnosticsFeature:
        return DummyDiagnosticsFeature()

    def app_factory() -> ApplicationFeature:
        return ApplicationFeature(ApplicationConfig(port=8080))

    async def _test() -> None:
        async with Runtime((diag_factory, app_factory)) as runtime:
            gw = runtime.require(GATEWAY_APPLICATION)
            info = gw.get_server_info()
            assert info.port == 8080
            assert "/healthz" in info.active_routes

            # Verify backward compatibility token
            http_legacy = runtime.require(HTTP_SERVER)
            assert http_legacy.get_server_info().port == 8080

    asyncio.run(_test())
