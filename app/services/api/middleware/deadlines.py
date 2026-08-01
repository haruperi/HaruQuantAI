"""Bounded deadlines for non-streaming API requests."""

from __future__ import annotations

import asyncio
from typing import override

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


class DeadlineMiddleware(BaseHTTPMiddleware):
    """Return a structured timeout when route handling exceeds its deadline."""

    def __init__(self, app: ASGIApp, *, timeout_seconds: float) -> None:
        """Create middleware with one validated positive deadline.

        Raises:
            ValueError: If the deadline is not positive.
        """
        super().__init__(app)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._timeout_seconds = timeout_seconds

    @override
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Bound one non-streaming route invocation.

        Returns:
            The delegated response or a structured timeout response.
        """
        try:
            async with asyncio.timeout(self._timeout_seconds):
                return await call_next(request)
        except TimeoutError:
            return JSONResponse({"detail": "UPSTREAM_TIMEOUT"}, status_code=504)


__all__ = ("DeadlineMiddleware",)
