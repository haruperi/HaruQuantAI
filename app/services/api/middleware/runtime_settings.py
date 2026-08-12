"""Per-request re-entry of composition-root DATA runtime settings.

`ContextVar.set()` inside the FastAPI `lifespan` only lives in the lifespan
task; Starlette dispatches each request as its own task, which never inherits
that context. Values set once during startup (`data_settings_context`,
`data_provider_settings_context`, `data_provider_connection_resolver_context`)
are therefore invisible to every route handler. This middleware re-enters
those same contexts, sourced from the values `lifecycle.py` cached on
`app.state`, for the single task that serves this request — the standard fix
for a lifespan-scoped ContextVar that a route handler needs to see.
"""

from __future__ import annotations

from typing import override

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.services.data import (
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    data_settings_context,
)


class RuntimeSettingsMiddleware(BaseHTTPMiddleware):
    """Re-establish composition-root DATA settings for one request's task."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the ASGI app with per-request DATA settings propagation."""
        super().__init__(app)

    @override
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Re-enter the cached DATA settings contexts for this request.

        Returns:
            The delegated response.
        """
        state = request.app.state
        data_settings = getattr(state, "api_data_settings", None)
        provider_settings = getattr(state, "api_data_provider_settings", None)
        connection_resolver = getattr(
            state, "api_data_provider_connection_resolver", None
        )
        if (
            data_settings is None
            or provider_settings is None
            or connection_resolver is None
        ):
            return await call_next(request)
        with (
            data_settings_context(data_settings),
            data_provider_settings_context(provider_settings),
            data_provider_connection_resolver_context(connection_resolver),
        ):
            return await call_next(request)


__all__ = ("RuntimeSettingsMiddleware",)
