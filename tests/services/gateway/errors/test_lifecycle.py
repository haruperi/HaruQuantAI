"""Lifecycle tests for gateway errors feature."""

from __future__ import annotations

import asyncio

from app.contracts.gateway import GATEWAY_ERRORS
from app.kernel.bootstrapper import Runtime
from app.services.gateway.errors import ErrorsFeature


def test_errors_lifecycle() -> None:
    """Test standard feature composition lifecycle."""

    async def _run() -> None:
        async with Runtime((ErrorsFeature,)) as runtime:
            mapper = runtime.require(GATEWAY_ERRORS)
            problem = mapper.to_problem_details(RuntimeError("test"))
            assert problem.status == 500

    asyncio.run(_run())
