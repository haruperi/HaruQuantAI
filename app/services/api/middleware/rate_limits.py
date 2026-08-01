"""Deterministic in-process rate limiting for registered API route classes."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Mapping
from typing import override

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply bounded fixed-window limits before route delegation."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        limits: Mapping[str, tuple[int, float]],
    ) -> None:
        """Create a limiter from explicitly configured route classes."""
        super().__init__(app)
        self._limits = dict(limits)
        self._observations: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    @staticmethod
    def _actor_key(request: Request) -> str:
        """Return a bounded principal or connection identity."""
        context = getattr(request.state, "api_request_context", None)
        actor_id = getattr(context, "actor_id", None)
        if actor_id:
            return str(actor_id)
        client = request.client
        return client.host if client is not None else "unknown"

    @override
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Reject requests that exceed their registered route-class limit.

        Returns:
            The delegated response or a structured rate-limit response.
        """
        registry = request.app.state.api_route_contract_registry
        contract = registry.get(request.method, request.url.path)
        rate_class = getattr(contract, "rate_limit", None)
        if rate_class is None:
            return await call_next(request)
        configured = self._limits.get(rate_class)
        if configured is None:
            return JSONResponse({"detail": "DEPENDENCY_UNAVAILABLE"}, status_code=503)
        capacity, window_seconds = configured
        now = time.monotonic()
        key = (rate_class, self._actor_key(request))
        with self._lock:
            observations = self._observations[key]
            cutoff = now - window_seconds
            while observations and observations[0] <= cutoff:
                observations.popleft()
            if len(observations) >= capacity:
                return JSONResponse(
                    {"detail": "RATE_LIMITED"},
                    status_code=429,
                    headers={"Retry-After": str(max(1, int(window_seconds)))},
                )
            observations.append(now)
        return await call_next(request)


__all__ = ("RateLimitMiddleware",)
