"""Lifecycle and composition tests for gateway authorization."""

from __future__ import annotations

import asyncio

from app.contracts.gateway import GATEWAY_AUTHORIZATION
from app.kernel.bootstrapper import Runtime
from app.services.gateway.authorization import (
    AuthorizationConfig,
    AuthorizationFeature,
)


def test_authorization_lifecycle() -> None:
    """Test standard feature composition lifecycle."""

    def auth_factory() -> AuthorizationFeature:
        return AuthorizationFeature(AuthorizationConfig(token_auth_enabled=False))

    async def _run() -> None:
        async with Runtime((auth_factory,)) as runtime:
            auth = runtime.require(GATEWAY_AUTHORIZATION)
            ctx = auth.authenticate_request({}, "127.0.0.1")
            assert ctx.authenticated

    asyncio.run(_run())
