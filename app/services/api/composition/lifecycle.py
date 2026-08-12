"""Required UI/API startup, readiness, and shutdown lifecycle."""

from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import ExitStack, asynccontextmanager
from typing import Any, Protocol, cast

from fastapi import FastAPI

from app.services.analytics import run_analytics_migrations
from app.services.api.composition.broker_config import (
    build_system_broker_connection_config,
)
from app.services.api.composition.migrations import run_api_migrations
from app.services.api.composition.runtime_settings import (
    activate_runtime_logging,
    build_runtime_data_provider_sources,
    build_runtime_provider_settings,
    load_runtime_settings_snapshot,
)
from app.services.brokers import run_broker_migrations
from app.services.data import (
    build_data_settings,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    data_settings_context,
)
from app.services.indicators import run_indicators_migrations
from app.services.optimization import run_optimization_migrations
from app.services.portfolio import run_portfolio_migrations
from app.services.simulator import run_simulator_migrations
from app.utils import generate_id, get_logger

logger = get_logger(__name__)


class StartupError(RuntimeError):
    """Required UI/API dependency failed to initialize."""


class _MigrationResponse(Protocol):
    """Migration response fields consumed by lifecycle."""

    status: str
    data: object | None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: C901, PLR0912, PLR0915
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
    with ExitStack() as settings_stack:
        settings_stack.enter_context(data_settings_context(data_settings))
        result = cast(
            "_MigrationResponse",
            run_api_migrations(generate_id("req")),
        )
        if result.status != "success" or result.data is None:
            app.state.api_ready = False
            raise StartupError("API_STORAGE_INITIALIZATION_FAILED")
        app.state.api_runtime_settings = load_runtime_settings_snapshot(
            request_id=generate_id("req")
        )
        try:
            activate_runtime_logging(app.state.api_runtime_settings)
        except (TypeError, ValueError) as error:
            app.state.api_ready = False
            raise StartupError("API_LOGGING_CONFIGURATION_INVALID") from error
        try:
            provider_settings = build_runtime_provider_settings(
                app.state.api_runtime_settings
            )

            def _resolve_connection(broker_id: str, request_id: str) -> object:
                """Resolve one broker connection config for the active session.

                Returns:
                    Composed broker connection configuration.
                """
                return build_system_broker_connection_config(
                    broker_id,
                    request_id=request_id,
                )

            enabled_sources = build_runtime_data_provider_sources(provider_settings)
            merged_sources = tuple(
                sorted(set(data_settings.data_provider_sources) | set(enabled_sources))
            )
            effective_data_settings = (
                data_settings
                if merged_sources == data_settings.data_provider_sources
                else data_settings.model_copy(
                    update={"data_provider_sources": merged_sources}
                )
            )
            # Also cache on `app.state`: a ContextVar `.set()` here lives in the
            # lifespan task and never propagates to per-request tasks, so
            # `RuntimeSettingsMiddleware` re-enters these contexts on every
            # request from these cached values. The lifespan-scoped context
            # entries below remain useful for code that runs directly within
            # startup (migrations, startup probes).
            app.state.api_data_settings = effective_data_settings
            app.state.api_data_provider_settings = provider_settings
            app.state.api_data_provider_connection_resolver = _resolve_connection
            settings_stack.enter_context(data_settings_context(effective_data_settings))
            settings_stack.enter_context(
                data_provider_settings_context(provider_settings)
            )
            settings_stack.enter_context(
                data_provider_connection_resolver_context(_resolve_connection)
            )
        except (TypeError, ValueError) as error:
            app.state.api_ready = False
            raise StartupError("API_PROVIDER_CONFIGURATION_INVALID") from error
        indicators_result = cast(
            "_MigrationResponse",
            run_indicators_migrations(generate_id("req")),
        )
        if indicators_result.status != "success" or indicators_result.data is None:
            app.state.api_ready = False
            raise StartupError("INDICATORS_STORAGE_INITIALIZATION_FAILED")
        brokers_result = cast(
            "_MigrationResponse",
            run_broker_migrations(generate_id("req")),
        )
        if brokers_result.status != "success" or brokers_result.data is None:
            app.state.api_ready = False
            raise StartupError("BROKERS_STORAGE_INITIALIZATION_FAILED")
        simulator_result = cast(
            "_MigrationResponse",
            run_simulator_migrations(generate_id("req")),
        )
        if simulator_result.status != "success" or simulator_result.data is None:
            app.state.api_ready = False
            raise StartupError("SIMULATOR_STORAGE_INITIALIZATION_FAILED")
        analytics_result = cast(
            "_MigrationResponse",
            run_analytics_migrations(generate_id("req")),
        )
        if analytics_result.status != "success" or analytics_result.data is None:
            app.state.api_ready = False
            raise StartupError("ANALYTICS_STORAGE_INITIALIZATION_FAILED")
        optimization_result = cast(
            "_MigrationResponse",
            run_optimization_migrations(generate_id("req")),
        )
        if optimization_result.status != "success" or optimization_result.data is None:
            app.state.api_ready = False
            raise StartupError("OPTIMIZATION_STORAGE_INITIALIZATION_FAILED")
        portfolio_result = cast(
            "_MigrationResponse",
            run_portfolio_migrations(generate_id("req")),
        )
        if portfolio_result.status != "success" or portfolio_result.data is None:
            app.state.api_ready = False
            raise StartupError("PORTFOLIO_STORAGE_INITIALIZATION_FAILED")
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
