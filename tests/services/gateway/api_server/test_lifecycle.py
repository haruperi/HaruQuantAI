"""Unit tests for Gateway API server feature lifecycle."""

import asyncio

import pytest
import uvicorn
from app.contracts.gateway import HTTP_SERVER
from app.kernel.bootstrapper import Runtime
from app.services.gateway.api_server import (
    SPEC,
    ApiServerFeature,
    feature,
)


def test_feature_factory_and_spec() -> None:
    """Verify feature factory and spec properties."""
    feat = feature()
    assert isinstance(feat, ApiServerFeature)
    assert feat.spec == SPEC
    assert HTTP_SERVER in feat.spec.provides


def test_feature_lifecycle_within_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify feature start, capability publication, and clean shutdown in Runtime."""

    async def _mock_serve(self: uvicorn.Server) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(uvicorn.Server, "serve", _mock_serve)

    async def _test() -> None:
        async with Runtime((feature,)) as runtime:
            service = runtime.require(HTTP_SERVER)
            info = service.get_server_info()
            assert info.host == "127.0.0.1"
            assert info.port == 8000
            assert "/health" in info.active_routes

    asyncio.run(_test())
