"""Composition of canonical backtest execution behind the API boundary.

The gateway owns no part of the backtest itself. It composes two things the
Simulation domain deliberately does not own: how verified provider facts are
obtained (Brokers), and which runtime context a background run must re-enter
(Data settings established per request by ``RuntimeSettingsMiddleware``).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from app.services.simulator import (
    build_backtest_job_registry,
    create_backtest_provider_facts,
    create_backtest_run_config,
    execute_backtest_job_inspection,
    execute_backtest_job_operation,
    get_backtest_strategy_catalogue,
)
from app.utils import generate_id

if TYPE_CHECKING:
    from app.services.api.workstation.simulator.schemas import SimulatorRunRequest

type AuthContext = Any


def _load_provider_facts(source_id: str, symbol: str) -> object:
    """Connect the configured provider and read verified facts for one symbol.

    The adapter is deliberately left connected. MT5 exposes one process-global
    terminal handle, so disconnecting here would tear the session out from under
    the Data retrieval that runs moments later — and from the chart, markets, and
    snapshot surfaces that share it. Session lifetime belongs to composition,
    which already closes provider sessions at shutdown.

    Args:
        source_id: Configured broker-backed data source identifier.
        symbol: Provider-native instrument symbol.

    Returns:
        Verified ``ProviderFacts`` for the run.

    Raises:
        ValueError: If configuration, connection, or evidence retrieval fails.
    """
    from app.services.api.composition.broker_config import (
        build_system_broker_connection_config,
    )
    from app.services.brokers import (
        connect_broker,
        create_broker_adapter,
        disconnect_broker,
        dump_provider_specification_snapshot,
        get_broker_account_info,
        get_broker_id,
        get_broker_provider_specification,
    )

    config = cast(
        "Any",
        build_system_broker_connection_config(source_id, request_id=generate_id("req")),
    )
    response = cast(
        "Any", create_broker_adapter(cast("Any", get_broker_id(source_id)), config)
    )
    if response.error is not None or response.data is None:
        raise ValueError("BACKTEST_PROVIDER_ADAPTER_UNAVAILABLE")
    adapter = response.data
    connected = cast("Any", asyncio.run(connect_broker(adapter)))
    if connected.error is not None:
        asyncio.run(disconnect_broker(adapter))
        raise ValueError("BACKTEST_PROVIDER_CONNECTION_FAILED")
    specification_response = cast(
        "Any", asyncio.run(get_broker_provider_specification(adapter, symbol))
    )
    account_response = cast("Any", asyncio.run(get_broker_account_info(adapter)))
    if specification_response.error is not None or specification_response.data is None:
        raise ValueError("BACKTEST_PROVIDER_SPECIFICATION_UNAVAILABLE")
    if account_response.error is not None or account_response.data is None:
        raise ValueError("BACKTEST_PROVIDER_ACCOUNT_UNAVAILABLE")
    details = account_response.data.details
    if "leverage" not in details:
        raise ValueError("BACKTEST_PROVIDER_LEVERAGE_UNAVAILABLE")
    leverage = Decimal(str(details["leverage"]))
    if not leverage.is_finite() or leverage <= 0:
        raise ValueError("BACKTEST_PROVIDER_LEVERAGE_INVALID")
    return create_backtest_provider_facts(
        specification=dump_provider_specification_snapshot(specification_response.data),
        leverage=leverage,
        account_currency=str(account_response.data.currency),
    )


def build_api_backtest_registry(
    runtime_context: Callable[[], AbstractContextManager[Any]] | None = None,
) -> object:
    """Build the gateway-composed background backtest registry.

    Args:
        runtime_context: Factory for the Data runtime context a background run
            must re-enter, since it executes outside any request task.

    Returns:
        Opaque Simulation-owned job registry.
    """

    def facts_loader(config: object) -> object:
        """Load verified provider facts for one run configuration.

        Returns:
            Verified provider facts.
        """
        typed = cast("Any", config)
        return _load_provider_facts(typed.source_id, typed.symbol)

    return build_backtest_job_registry(
        facts_loader=facts_loader, runtime_context=runtime_context
    )


def build_data_runtime_context(
    state_provider: Callable[[], object],
) -> Callable[[], AbstractContextManager[Any]]:
    """Build a factory re-entering composition-root Data settings on a thread.

    Args:
        state_provider: Late-bound accessor for FastAPI application state. The
            graph is composed before the application object exists, so the
            state is resolved when a run actually starts.

    Returns:
        Callable producing the Data runtime context for one background run.
    """

    def factory() -> AbstractContextManager[Any]:
        """Enter the composed Data settings, or nothing when uncomposed.

        Returns:
            Context manager covering one background run.
        """
        from app.services.data import (
            data_provider_connection_resolver_context,
            data_provider_settings_context,
            data_settings_context,
        )

        app_state = state_provider()
        stack = ExitStack()
        settings = getattr(app_state, "api_data_settings", None)
        provider_settings = getattr(app_state, "api_data_provider_settings", None)
        resolver = getattr(app_state, "api_data_provider_connection_resolver", None)
        if settings is not None:
            stack.enter_context(data_settings_context(settings))
        if provider_settings is not None:
            stack.enter_context(data_provider_settings_context(provider_settings))
        if resolver is not None:
            stack.enter_context(data_provider_connection_resolver_context(resolver))
        return stack

    return factory


def build_simulator_strategy_source() -> Callable[[], tuple[object, ...]]:
    """Build the read operation returning the registered strategy catalogue.

    Returns:
        Callable delegating once to the Simulation public catalogue.
    """
    return get_backtest_strategy_catalogue


def build_simulator_run_source(registry: object | None) -> Callable[..., object]:
    """Build the dispatcher covering every Simulator run operation.

    Args:
        registry: Composed background registry, or ``None`` to fail closed.

    Returns:
        Callable dispatching one allowlisted registry operation.
    """

    def dispatch(operation: str, *args: object, **kwargs: object) -> object:
        """Execute one Simulator run operation.

        Returns:
            Registry or job operation result.

        Raises:
            RuntimeError: If the registry is not composed.
            ValueError: If the operation is unsupported.
        """
        if registry is None:
            raise RuntimeError("SIMULATOR_RUNTIME_UNAVAILABLE")
        if operation == "submit":
            request = cast("SimulatorRunRequest", args[0])
            principal_id = str(kwargs["principal_id"])
            config = create_backtest_run_config(
                symbol=request.symbol,
                timeframe=request.timeframe,
                start=request.start,
                end=request.end,
                strategy_id=request.strategy_id,
                parameters=dict(request.parameters),
                initial_balance=request.initial_balance,
                account_currency=request.account_currency,
                volume=request.volume,
                commission_per_lot_per_side=request.commission_per_lot_per_side,
                spread_points=request.spread_points,
                slippage_points=request.slippage_points,
                seed=request.seed,
                bar_limit=request.bar_limit,
                account_id=principal_id,
            )
            job = execute_backtest_job_operation(
                registry, "submit", config, principal_id=principal_id
            )
            return execute_backtest_job_inspection(job, "snapshot")
        if operation in {"cancel", "get", "stream"}:
            job = execute_backtest_job_operation(
                registry, "get", str(args[0]), principal_id=str(kwargs["principal_id"])
            )
            if job is None:
                return None
            if operation == "get":
                return execute_backtest_job_inspection(job, "snapshot")
            if operation == "cancel":
                execute_backtest_job_inspection(job, "request_cancel")
                return execute_backtest_job_inspection(job, "snapshot")
            return execute_backtest_job_operation(
                registry, "stream", job, after=int(cast("int", kwargs["after"]))
            )
        if operation == "list":
            jobs = execute_backtest_job_operation(
                registry, "list_jobs", principal_id=str(kwargs["principal_id"])
            )
            return tuple(
                execute_backtest_job_inspection(job, "snapshot")
                for job in cast("tuple[Any, ...]", jobs)
            )
        raise ValueError("unsupported Simulator run operation")

    return dispatch


__all__ = (
    "build_api_backtest_registry",
    "build_data_runtime_context",
    "build_simulator_run_source",
    "build_simulator_strategy_source",
)
