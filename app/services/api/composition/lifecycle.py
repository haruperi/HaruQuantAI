"""Required UI/API startup, readiness, and shutdown lifecycle."""

from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from typing import Any, Protocol, cast

from fastapi import FastAPI

from app.services.api.identity import run_api_migrations
from app.services.data import build_data_settings, data_settings_context
from app.utils import generate_id, get_logger

logger = get_logger(__name__)


class StartupError(RuntimeError):
    """Required UI/API dependency failed to initialize."""


class _MigrationResponse(Protocol):
    """Migration response fields consumed by lifecycle."""

    status: str
    data: object | None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize required storage and close gateway-owned resources.

    Args:
        app: Canonical FastAPI application.

    Yields:
        Control to the running application after required initialization.

    Raises:
        StartupError: If required API storage initialization fails.
    """
    logger.info("Starting canonical UI/API lifecycle")
    data_settings = build_data_settings()
    with data_settings_context(data_settings):
        result = cast(
            "_MigrationResponse",
            run_api_migrations(generate_id("req")),
        )
        if result.status != "success" or result.data is None:
            app.state.api_ready = False
            raise StartupError("API_STORAGE_INITIALIZATION_FAILED")
        required_probes: Mapping[str, Callable[[], object]] = getattr(
            app.state,
            "api_required_startup_probes",
            {},
        )
        for name, probe in required_probes.items():
            try:
                dependency = probe()
            except Exception as error:
                app.state.api_ready = False
                logger.exception("Required API dependency unavailable: %s", name)
                message = f"API_REQUIRED_DEPENDENCY_UNAVAILABLE:{name}"
                raise StartupError(message) from error
            if dependency is None:
                app.state.api_ready = False
                message = f"API_REQUIRED_DEPENDENCY_UNAVAILABLE:{name}"
                raise StartupError(message)
        app.state.api_ready = True
        optional_probes: Mapping[str, Callable[[], object]] = getattr(
            app.state,
            "api_optional_startup_probes",
            {},
        )
        degraded: dict[str, str] = {}
        for name, probe in optional_probes.items():
            try:
                probe()
            except Exception:  # Optional adapters degrade without changing truth.
                logger.exception("Optional API dependency unavailable: %s", name)
                degraded[name] = "DEPENDENCY_UNAVAILABLE"
        app.state.api_optional_degraded = degraded
        try:
            yield
        finally:
            closers: tuple[Callable[[], Any], ...] = getattr(
                app.state,
                "api_owned_resource_closers",
                (),
            )
            for close in reversed(closers):
                close()
            app.state.api_ready = False
            logger.info("Stopped canonical UI/API lifecycle")


__all__ = ("StartupError", "lifespan")
