"""Required UI/API startup, readiness, and shutdown lifecycle."""

from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import ExitStack, asynccontextmanager
from typing import Any, Protocol, cast

from fastapi import FastAPI

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.services.api.composition.broker_config import (
    build_system_broker_connection_config,
)
from app.services.api.composition.capabilities import (
    get_inactive_capabilities,
    import_capability_attribute,
)
from app.services.api.composition.migrations import run_api_migrations
from app.services.api.composition.runtime_settings import (
    activate_runtime_logging,
    build_runtime_data_provider_sources,
    build_runtime_provider_settings,
    load_runtime_settings_snapshot,
)
from app.services.data import (
    build_data_settings,
    close_data_provider_sessions,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    data_settings_context,
)
from app.services.indicators import run_indicators_migrations
from app.services.simulator import run_simulator_migrations
from app.services.trading import run_trading_migrations

logger = get_logger(__name__)

# Optional-capability migrations resolve tolerantly. An absent capability
# supplies no migration and is reported degraded; required storage migrations
# remain fatal. Broker provider lifecycle is owned by Composition/FeatureScope,
# not by the API process lifecycle.
_OPTIONAL_MIGRATIONS: tuple[tuple[str, str, str, str], ...] = (
    (
        "analytics",
        "app.services.analytics",
        "run_analytics_migrations",
        "ANALYTICS_STORAGE_INITIALIZATION_FAILED",
    ),
    (
        "optimization",
        "app.services.optimization",
        "run_optimization_migrations",
        "OPTIMIZATION_STORAGE_INITIALIZATION_FAILED",
    ),
    (
        "portfolio",
        "app.services.portfolio",
        "run_portfolio_migrations",
        "PORTFOLIO_STORAGE_INITIALIZATION_FAILED",
    ),
)


def _run_optional_migrations(degraded: dict[str, str]) -> None:
    """Apply optional-capability migrations without blocking startup.

    Args:
        degraded: Mutable record of capability identifier to degradation reason.
    """
    for capability_id, module_path, attribute, reason in _OPTIONAL_MIGRATIONS:
        migration = import_capability_attribute(
            module_path,
            attribute,
            capability_id=capability_id,
        )
        if migration is None:
            degraded[capability_id] = "CAPABILITY_ABSENT"
            continue
        try:
            result = cast(
                "_MigrationResponse", cast("Any", migration)(generate_id("req"))
            )
        except Exception:  # Optional storage degrades without changing truth.
            logger.exception("Optional capability migration failed: %s", capability_id)
            degraded[capability_id] = reason
            continue
        if result.status != "success" or result.data is None:
            logger.warning("Optional capability storage unavailable: %s", capability_id)
            degraded[capability_id] = reason


class StartupError(RuntimeError):
    """Required UI/API dependency failed to initialize."""


class _MigrationResponse(Protocol):
    """Migration response fields consumed by lifecycle."""

    status: str
    data: object | None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: C901, PLR0912, PLR0915
    """Initialize required storage and database-configured gateway resources.

    Broker providers are discovered, mounted, and disposed by Composition and
    FeatureScope. This lifecycle must not create a second Broker service locator,
    run a Broker-global migration, or manually start an MT5 background gateway.

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
                """Resolve one legacy Data-provider connection configuration.

                This compatibility callback remains until the Data domain consumes
                provider capabilities directly. It does not own Broker lifecycle.

                Args:
                    broker_id: Exact configured provider identifier.
                    request_id: Trace identifier for the resolution request.

                Returns:
                    Composed connection configuration.
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
            # request from these cached values.
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
        simulator_result = cast(
            "_MigrationResponse",
            run_simulator_migrations(generate_id("req")),
        )
        if simulator_result.status != "success" or simulator_result.data is None:
            app.state.api_ready = False
            raise StartupError("SIMULATOR_STORAGE_INITIALIZATION_FAILED")
        trading_result = cast(
            "_MigrationResponse",
            run_trading_migrations(request_id=generate_id("req")),
        )
        if trading_result.status != "success" or trading_result.data is None:
            app.state.api_ready = False
            raise StartupError("TRADING_STORAGE_INITIALIZATION_FAILED")
        degraded: dict[str, str] = dict(get_inactive_capabilities())
        _run_optional_migrations(degraded)
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
            provider_close_result = close_data_provider_sessions(generate_id("req"))
            if provider_close_result.status != "success":
                logger.warning("Data provider-session shutdown failed")
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
