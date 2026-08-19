"""Function-only public boundary for the Simulation domain."""

# The root gate intentionally resolves internal callables lazily and exposes
# uniform response wrappers whose concrete return types remain domain-private.
# ruff: noqa: ANN401, DOC201

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from importlib import import_module
from typing import Any, Literal, Protocol, cast


class StandardResponse[T](Protocol):
    """Opaque structural public response carrying one typed payload."""

    @property
    def data(self) -> T | None:
        """Return successful response data."""
        ...


RiskLevel = Literal["none", "low", "medium", "high", "critical"]

_VALUE_TYPES: Mapping[str, tuple[str, str]] = {
    "AccountingSummary": ("app.services.simulator.reporting", "AccountingSummary"),
    "ArtifactEntry": ("app.services.simulator.reporting", "ArtifactEntry"),
    "ArtifactManifest": ("app.services.simulator.reporting", "ArtifactManifest"),
    "ClosedTradeRecord": ("app.services.simulator.reporting", "ClosedTradeRecord"),
    "ComponentReturnSeries": (
        "app.services.simulator.reporting",
        "ComponentReturnSeries",
    ),
    "ExecutionCostInput": ("app.services.simulator.accounting", "ExecutionCostInput"),
    "ExecutionCostModel": ("app.services.simulator.accounting", "ExecutionCostModel"),
    "ExecutionProfile": ("app.services.simulator.execution", "ExecutionProfile"),
    "FastResearchResult": ("app.services.simulator.reporting", "FastResearchResult"),
    "JournalEvent": ("app.services.simulator.journal", "JournalEvent"),
    "LedgerFill": ("app.services.simulator.accounting", "LedgerFill"),
    "MarketDataValidationContext": (
        "app.services.simulator.validation.contracts",
        "MarketDataValidationContext",
    ),
    "MarketEvidenceLineage": (
        "app.services.simulator.validation.contracts",
        "MarketEvidenceLineage",
    ),
    "MatchResult": ("app.services.simulator.execution", "MatchResult"),
    "PortfolioBacktestRequest": (
        "app.services.simulator.run",
        "PortfolioBacktestRequest",
    ),
    "PortfolioComponentRequest": (
        "app.services.simulator.run",
        "PortfolioComponentRequest",
    ),
    "PortfolioComponentResult": (
        "app.services.simulator.reporting",
        "PortfolioComponentResult",
    ),
    "PortfolioSimulationResult": (
        "app.services.simulator.reporting",
        "PortfolioSimulationResult",
    ),
    "RealismDisclosure": ("app.services.simulator.reporting", "RealismDisclosure"),
    "ReturnObservation": ("app.services.simulator.reporting", "ReturnObservation"),
    "RiskBudgetHistoryRow": (
        "app.services.simulator.reporting",
        "RiskBudgetHistoryRow",
    ),
    "SessionInterval": ("app.services.simulator.execution", "SessionInterval"),
    "FastResearchRequest": (
        "app.services.simulator.run",
        "FastResearchRequest",
    ),
    "SimulationBacktestRequest": (
        "app.services.simulator.run",
        "SimulationBacktestRequest",
    ),
    "SimulationResult": ("app.services.simulator.reporting", "SimulationResult"),
    "SymbolSpecification": (
        "app.services.simulator.accounting",
        "SymbolSpecification",
    ),
    "Tick": ("app.services.simulator.timeline", "Tick"),
    "ValidatedFXConversionEvidence": (
        "app.services.simulator.accounting",
        "ValidatedFXConversionEvidence",
    ),
    "ValidatedMarketDataEvidence": (
        "app.services.simulator.validation.contracts",
        "ValidatedMarketDataEvidence",
    ),
}

_HANDLE_TYPES: Mapping[str, tuple[str, str]] = {
    "AccountLedger": ("app.services.simulator.accounting", "AccountLedger"),
    "EventDrivenExecutionEngine": (
        "app.services.simulator.execution",
        "EventDrivenExecutionEngine",
    ),
    "JournalWriter": ("app.services.simulator.journal", "JournalWriter"),
    "SimTrader": ("app.services.simulator.execution", "SimTrader"),
}

_HANDLE_OPERATIONS: Mapping[str, frozenset[str]] = {
    "AccountLedger": frozenset(
        {"apply_fill", "mark_to_market", "snapshot", "validate_invariants"}
    ),
    "EventDrivenExecutionEngine": frozenset(
        {
            "cancel_order",
            "close_position",
            "execute_tick",
            "snapshot",
            "submit_order",
        }
    ),
    "JournalWriter": frozenset({"append", "finalize"}),
    "SimTrader": frozenset(
        {
            "cancel_order",
            "close_position",
            "get_account",
            "get_order",
            "get_positions",
            "snapshot",
            "submit_order",
        }
    ),
}


def _guarded[**P, T](
    function: Callable[P, T],
    *,
    operation: str,
    risk_level: RiskLevel,
    read_only: bool,
    writes_file: bool = False,
    modifies_database: bool = False,
) -> Callable[P, StandardResponse[T]]:
    """Return one canonical guarded Simulation operation."""
    from app.services.simulator.errors import guard_operation

    return cast(
        "Callable[P, StandardResponse[T]]",
        guard_operation(
            function,
            operation=operation,
            risk_level=risk_level,
            read_only=read_only,
            writes_file=writes_file,
            modifies_database=modifies_database,
        ),
    )


def _guarded_async[**P, T](
    function: Callable[P, Awaitable[T]],
    *,
    operation: str,
    risk_level: RiskLevel,
    read_only: bool,
    writes_file: bool = False,
    modifies_database: bool = False,
) -> Callable[P, Awaitable[StandardResponse[T]]]:
    """Return one canonical guarded asynchronous Simulation operation."""
    from app.services.simulator.errors import guard_async_operation

    return cast(
        "Callable[P, Awaitable[StandardResponse[T]]]",
        guard_async_operation(
            function,
            operation=operation,
            risk_level=risk_level,
            read_only=read_only,
            writes_file=writes_file,
            modifies_database=modifies_database,
        ),
    )


def _resolve(registry: Mapping[str, tuple[str, str]], name: str) -> Any:
    """Resolve one internal implementation lazily from an approved registry.

    Returns:
        Resolved internal implementation.

    Raises:
        ValueError: If the name is not registered.
    """
    target = registry.get(name)
    if target is None:
        raise ValueError("unsupported public Simulation type")
    module_name, attribute = target
    return getattr(import_module(module_name), attribute)


def _operation(module: str, name: str) -> Callable[..., object]:
    """Resolve one internal operation lazily.

    Returns:
        Resolved internal operation.
    """
    return cast("Callable[..., object]", getattr(import_module(module), name))


def create_simulation_value(value_type: str, /, **fields: object) -> object:
    """Create one documented opaque Simulation contract value.

    Args:
        value_type: Registered Simulation value name.
        **fields: Constructor fields for the selected value.

    Returns:
        The validated opaque Simulation value.

    Raises:
        ValueError: If the value type is not part of the public catalogue.
    """
    model = _resolve(_VALUE_TYPES, value_type)
    return model(**fields)


def build_simulation_run_dependencies(**values: object) -> object:
    """Build one explicit canonical Simulation runtime dependency bundle.

    Args:
        **values: Exact state, artifact, policy, and public owner ports.

    Returns:
        Opaque dependency bundle accepted by ``run_backtest_async``.
    """
    builder = _operation(
        "app.services.simulator.run.dependencies",
        "build_simulation_run_dependencies",
    )
    return builder(**cast("Any", values))


def get_backtest_strategy_catalogue() -> tuple[Mapping[str, object], ...]:
    """Return every registered backtest strategy as bounded public evidence.

    Each entry declares the strategy's identity, its configuration parameters,
    and whether the canonical recipe can run it today. A strategy that cannot
    run stays listed and carries the exact reason.

    Returns:
        Serializable descriptor projections in stable registration order.
    """
    from app.services.simulator.backtest_recipe import (
        get_backtest_strategy_descriptors,
    )

    return tuple(
        {
            "strategy_id": descriptor.strategy_id,
            "strategy_version": descriptor.strategy_version,
            "evaluator_name": descriptor.evaluator_name,
            "label": descriptor.label,
            "runnable": descriptor.runnable,
            "unavailable_reason": descriptor.unavailable_reason,
            "required_indicators": descriptor.required_indicators,
            "supports_exits": bool(
                descriptor.long_exit_signals or descriptor.short_exit_signals
            ),
            "parameters": tuple(
                {
                    "name": item.name,
                    "label": item.label,
                    "kind": item.kind,
                    "default": item.default,
                    "minimum": item.minimum,
                    "maximum": item.maximum,
                }
                for item in descriptor.parameters
            ),
        }
        for descriptor in get_backtest_strategy_descriptors()
    )


def create_backtest_provider_facts(**values: object) -> object:
    """Create one verified provider-facts value for a backtest run.

    Args:
        **values: ``specification``, ``leverage``, and ``account_currency``.

    Returns:
        Opaque provider-facts value accepted by the backtest recipe.
    """
    from app.services.simulator.backtest_recipe import ProviderFacts

    return ProviderFacts(**cast("Any", values))


def create_backtest_run_config(**values: object) -> object:
    """Create one validated canonical backtest run configuration.

    Args:
        **values: Operator-chosen run configuration fields.

    Returns:
        Opaque validated run configuration.
    """
    from app.services.simulator.backtest_recipe import BacktestRunConfig

    config = BacktestRunConfig(**cast("Any", values))
    config.validate()
    return config


def build_backtest_job_registry(**values: object) -> object:
    """Build one bounded background registry for canonical backtest runs.

    Args:
        **values: ``facts_loader`` and optional ``max_jobs`` bound.

    Returns:
        Opaque job registry handle.
    """
    from app.services.simulator.backtest_recipe import BacktestJobRegistry

    return BacktestJobRegistry(**cast("Any", values))


def execute_backtest_job_operation(
    registry: object,
    operation: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Execute one allowlisted operation on a backtest job registry.

    Args:
        registry: Opaque registry handle.
        operation: Allowlisted registry operation name.
        *args: Positional operation arguments.
        **kwargs: Keyword operation arguments.

    Returns:
        Exact registry operation response.

    Raises:
        TypeError: If the handle is not a backtest job registry.
        ValueError: If the operation is not part of the registry boundary.
    """
    from app.services.simulator.backtest_recipe import BacktestJobRegistry

    allowed = {"get", "list_jobs", "stream", "submit"}
    if not isinstance(registry, BacktestJobRegistry):
        raise TypeError("registry must be a BacktestJobRegistry")
    if operation not in allowed:
        raise ValueError("unsupported backtest job registry operation")
    return getattr(registry, operation)(*args, **kwargs)


def execute_backtest_job_inspection(job: object, operation: str, /) -> object:
    """Execute one allowlisted read or cancellation on a backtest job.

    Args:
        job: Opaque job handle returned by the registry.
        operation: Either ``snapshot`` or ``request_cancel``.

    Returns:
        Bounded job projection or cancellation outcome.

    Raises:
        TypeError: If the handle is not a backtest job.
        ValueError: If the operation is not part of the job boundary.
    """
    from app.services.simulator.backtest_recipe import BacktestJob

    if not isinstance(job, BacktestJob):
        raise TypeError("job must be a BacktestJob")
    if operation not in {"request_cancel", "snapshot"}:
        raise ValueError("unsupported backtest job operation")
    return getattr(job, operation)()


def build_simulation_state_store(**values: object) -> object:
    """Build the durable Simulation state adapter.

    Returns:
        Opaque state-store implementation.
    """
    from app.services.simulator.state import build_simulation_state_store as builder

    return builder(**cast("Any", values))


def execute_simulation_state_store_operation(
    store: object,
    operation: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Execute one allowlisted operation on a Simulation state adapter.

    Returns:
        Exact state operation response.

    Raises:
        TypeError: If the handle does not satisfy the Simulation state protocol.
        ValueError: If the operation is not part of the state boundary.
    """
    from app.services.simulator.state import SimulationStateStore

    allowed = {
        "append_journal",
        "finalize_journal",
        "flush_journal",
        "load_result",
        "load_run",
        "record_idempotency",
    }
    if not isinstance(store, SimulationStateStore):
        raise TypeError("store must implement SimulationStateStore")
    if operation not in allowed:
        raise ValueError("unsupported Simulation state-store operation")
    return getattr(store, operation)(*args, **kwargs)


def get_simulation_result(run_id: str, **values: object) -> object | None:
    """Read one validated completed Simulation result by run ID.

    Args:
        run_id: Canonical Simulation run identifier.
        **values: State-store construction values, including ``artifact_root``.

    Returns:
        Canonical result or ``None`` when the run is unknown or incomplete.
    """
    store = build_simulation_state_store(**values)
    return execute_simulation_state_store_operation(store, "load_result", run_id)


def create_simulation_session(
    run_id: str, *, request_id: str
) -> StandardResponse[object]:
    """Create one journal playback session for a completed run."""
    return _guarded(
        _operation("app.services.simulator.state", "create_simulation_session"),
        operation="simulation.state.create_simulation_session",
        risk_level="low",
        read_only=False,
        modifies_database=True,
    )(run_id, request_id=request_id)


def create_live_simulation_session(
    request: object,
    dependencies: object,
    *,
    request_id: str,
    durable: bool = False,
) -> StandardResponse[object]:
    """Open one bounded live what-if session over a prepared run."""
    return _guarded(
        _operation("app.services.simulator.state", "create_live_simulation_session"),
        operation="simulation.state.create_live_simulation_session",
        risk_level="low",
        read_only=False,
        modifies_database=durable,
    )(request, dependencies, request_id=request_id, durable=durable)


def restore_live_simulation_session(
    session_id: str, dependencies: object, *, request_id: str
) -> StandardResponse[object]:
    """Reconstruct one durable session and leave it recovery-blocked."""
    return _guarded(
        _operation("app.services.simulator.state", "restore_live_simulation_session"),
        operation="simulation.state.restore_live_simulation_session",
        risk_level="high",
        read_only=False,
        modifies_database=True,
    )(session_id, dependencies, request_id=request_id)


def rearm_live_simulation_session(
    session_id: str, *, approved: bool, request_id: str
) -> StandardResponse[object]:
    """Explicitly rearm one verified reconstructed session."""
    return _guarded(
        _operation("app.services.simulator.state", "rearm_live_simulation_session"),
        operation="simulation.state.rearm_live_simulation_session",
        risk_level="high",
        read_only=False,
        modifies_database=True,
    )(session_id, approved=approved, request_id=request_id)


def step_live_simulation(session_id: str, ticks: int) -> StandardResponse[object]:
    """Advance one live what-if session by a bounded number of ticks."""
    return _guarded(
        _operation("app.services.simulator.state", "step_live_simulation"),
        operation="simulation.state.step_live_simulation",
        risk_level="low",
        read_only=False,
        modifies_database=False,
    )(session_id, ticks)


async def submit_live_simulation_order(
    session_id: str, intent: object
) -> StandardResponse[object]:
    """Submit an unchanged approved intent to one historical session."""
    return await _guarded_async(
        cast(
            "Any",
            _operation("app.services.simulator.state", "submit_live_simulation_order"),
        ),
        operation="simulation.state.submit_live_simulation_order",
        risk_level="medium",
        read_only=False,
        modifies_database=False,
    )(session_id, intent)


def list_live_simulation_sessions() -> StandardResponse[object]:
    """List every live what-if session this process currently holds."""
    return _guarded(
        _operation("app.services.simulator.state", "list_live_simulation_sessions"),
        operation="simulation.state.list_live_simulation_sessions",
        risk_level="low",
        read_only=True,
        modifies_database=False,
    )()


def seek_live_simulation(
    session_id: str, target_cursor: int
) -> StandardResponse[object]:
    """Advance one live what-if session forward to an absolute cursor."""
    return _guarded(
        _operation("app.services.simulator.state", "seek_live_simulation"),
        operation="simulation.state.seek_live_simulation",
        risk_level="low",
        read_only=False,
        modifies_database=False,
    )(session_id, target_cursor)


async def execute_live_simulation_command(
    session_id: str, command: object
) -> StandardResponse[object]:
    """Execute one manual command and return its receipt and refreshed state."""
    return await _guarded_async(
        cast(
            "Any",
            _operation(
                "app.services.simulator.state", "execute_live_simulation_command"
            ),
        ),
        operation="simulation.state.execute_live_simulation_command",
        risk_level="medium",
        read_only=False,
        modifies_database=False,
    )(session_id, command)


def finalize_live_simulation_session(
    session_id: str, *, request_id: str
) -> StandardResponse[object]:
    """Seal one live what-if session advisory journal."""
    return _guarded(
        _operation("app.services.simulator.state", "finalize_live_simulation_session"),
        operation="simulation.state.finalize_live_simulation_session",
        risk_level="medium",
        read_only=False,
        modifies_database=True,
    )(session_id, request_id=request_id)


def read_live_simulation_state(session_id: str) -> StandardResponse[object]:
    """Read one live what-if session projection."""
    return _guarded(
        _operation("app.services.simulator.state", "read_live_simulation_state"),
        operation="simulation.state.read_live_simulation_state",
        risk_level="low",
        read_only=True,
        modifies_database=False,
    )(session_id)


def read_live_simulation_viewport(
    session_id: str, *, before: int = 300
) -> StandardResponse[object]:
    """Read one bounded backwards-only market viewport for a live session."""
    return _guarded(
        _operation("app.services.simulator.state", "read_live_simulation_viewport"),
        operation="simulation.state.read_live_simulation_viewport",
        risk_level="low",
        read_only=True,
        modifies_database=False,
    )(session_id, before=before)


def branch_live_simulation(
    session_id: str,
    overrides: Mapping[str, object],
    dependencies: object,
    *,
    request_id: str,
) -> StandardResponse[object]:
    """Fork one live session into an independent advisory what-if branch."""
    return _guarded(
        _operation("app.services.simulator.state", "branch_live_simulation"),
        operation="simulation.state.branch_live_simulation",
        risk_level="low",
        read_only=False,
        modifies_database=False,
    )(session_id, overrides, dependencies, request_id=request_id)


def close_live_simulation_session(session_id: str) -> StandardResponse[object]:
    """Close one live what-if session and release its engine."""
    return _guarded(
        _operation("app.services.simulator.state", "close_live_simulation_session"),
        operation="simulation.state.close_live_simulation_session",
        risk_level="low",
        read_only=False,
        modifies_database=False,
    )(session_id)


def reset_live_simulation_sessions() -> StandardResponse[object]:
    """Drop every live what-if session."""
    return _guarded(
        _operation("app.services.simulator.state", "reset_live_simulation_sessions"),
        operation="simulation.state.reset_live_simulation_sessions",
        risk_level="low",
        read_only=False,
        modifies_database=False,
    )()


def read_simulation_session(session_id: str) -> StandardResponse[object]:
    """Read one journal playback session projection."""
    return _guarded(
        _operation("app.services.simulator.state", "read_simulation_session"),
        operation="simulation.state.read_simulation_session",
        risk_level="low",
        read_only=True,
    )(session_id)


def stream_simulation_session_frames(
    session_id: str,
    *,
    resume_after: int | None,
    dependencies: object,
) -> object:
    """Return an async iterator over one playback session's journal frames."""
    operation = _operation(
        "app.services.simulator.state", "stream_simulation_session_frames"
    )
    return operation(
        session_id,
        resume_after=resume_after,
        dependencies=dependencies,
    )


def create_simulation_handle(
    handle_type: str, /, *args: object, **kwargs: object
) -> object:
    """Create one documented opaque stateful Simulation handle.

    Args:
        handle_type: Registered handle name.
        *args: Positional constructor arguments.
        **kwargs: Keyword constructor arguments.

    Returns:
        The initialized opaque Simulation handle.

    Raises:
        ValueError: If the handle type is not publicly supported.
    """
    handle = _resolve(_HANDLE_TYPES, handle_type)
    return handle(*args, **kwargs)


def execute_simulation_handle_operation(
    handle: object,
    operation: str,
    /,
    *args: object,
    **kwargs: object,
) -> object:
    """Execute one allow-listed operation on an opaque Simulation handle.

    Args:
        handle: Handle returned by :func:`create_simulation_handle`.
        operation: Registered operation for the handle type.
        *args: Positional operation arguments.
        **kwargs: Keyword operation arguments.

    Returns:
        The exact operation result, including awaitables for asynchronous handles.

    Raises:
        ValueError: If the handle or operation is not publicly supported.
    """
    for name in _HANDLE_TYPES:
        handle_type = _resolve(_HANDLE_TYPES, name)
        if isinstance(handle, handle_type):
            if operation not in _HANDLE_OPERATIONS[name]:
                raise ValueError("unsupported public Simulation handle operation")
            return getattr(handle, operation)(*args, **kwargs)
    raise ValueError("unsupported public Simulation handle")


def get_simulation_value_field(value: object, field: str) -> object:
    """Return one public field from an opaque Simulation value.

    Raises:
        ValueError: If the field is private or unavailable.
    """
    if not field or field.startswith("_") or not hasattr(value, field):
        raise ValueError("Simulation value does not expose the requested field")
    return getattr(value, field)


def get_simulation_value_fields(value_type: str) -> tuple[str, ...]:
    """Return the declared public fields for one Simulation value type."""
    model = _resolve(_VALUE_TYPES, value_type)
    fields = getattr(model, "model_fields", None)
    if isinstance(fields, Mapping):
        return tuple(fields)
    return tuple(getattr(model, "__dataclass_fields__", ()))


def is_simulation_value(value: object, value_type: str) -> bool:
    """Return whether a value has the selected internal Simulation contract type."""
    if value_type not in _VALUE_TYPES:
        return False
    return isinstance(value, _resolve(_VALUE_TYPES, value_type))


def dump_simulation_value(value: object) -> Mapping[str, object]:
    """Return a detached Python mapping for one opaque Simulation value.

    Raises:
        TypeError: If the value cannot produce a mapping.
    """
    dump = getattr(value, "model_dump", None)
    if not callable(dump):
        raise TypeError("Simulation value does not support mapping projection")
    result = dump(mode="python", warnings=False)
    if not isinstance(result, Mapping):
        raise TypeError("Simulation value projection is not a mapping")
    return dict(result)


def calculate_simulation_backtest_config_hash(
    payload: Mapping[str, object],
) -> StandardResponse[str]:
    """Calculate the canonical Simulation backtest configuration hash."""
    model = _resolve(_VALUE_TYPES, "SimulationBacktestRequest")
    return cast("StandardResponse[str]", model.calculate_config_hash(payload))


def calculate_fast_research_config_hash(
    payload: Mapping[str, object],
) -> StandardResponse[str]:
    """Calculate the explicitly non-canonical research configuration hash."""
    model = _resolve(_VALUE_TYPES, "FastResearchRequest")
    return cast("StandardResponse[str]", model.calculate_config_hash(payload))


def calculate_portfolio_backtest_config_hash(
    payload: Mapping[str, object],
) -> StandardResponse[str]:
    """Calculate the canonical portfolio backtest configuration hash."""
    model = _resolve(_VALUE_TYPES, "PortfolioBacktestRequest")
    return cast("StandardResponse[str]", model.calculate_config_hash(payload))


def get_approved_tick_models() -> tuple[str, ...]:
    """Return the approved deterministic tick-model names."""
    from app.services.simulator.timeline import APPROVED_TICK_MODELS

    return APPROVED_TICK_MODELS


def get_canonical_artifact_types() -> tuple[str, ...]:
    """Return the required canonical artifact type names."""
    from app.services.simulator.reporting import CANONICAL_ARTIFACT_TYPES

    return CANONICAL_ARTIFACT_TYPES


def get_journal_policy() -> Mapping[str, object]:
    """Return immutable journal format, durability, and sidecar policy."""
    from app.services.simulator.journal import (
        JOURNAL_FORMAT,
        JOURNAL_FSYNC_INTERVAL,
        JOURNAL_SIDECAR_MODE,
    )

    return {
        "format": JOURNAL_FORMAT,
        "fsync_interval": JOURNAL_FSYNC_INTERVAL,
        "sidecar_mode": JOURNAL_SIDECAR_MODE,
    }


def get_report_schema_version() -> str:
    """Return the canonical Simulation report schema version."""
    from app.services.simulator.reporting import REPORT_SCHEMA_VERSION

    return REPORT_SCHEMA_VERSION


def get_parity_envelope(version: str = "v1") -> Mapping[str, object]:
    """Return the published versioned Parity Envelope mapping.

    Args:
        version: Envelope version identifier; ``v1`` is the only published
            version of the MT5-FX demo matrix.

    Returns:
        Read-only envelope mapping (scope, invariants, route gate policies,
        ignored-field registry, initial authority state, validity, aggregate
        economic-error budget, invalidation triggers).

    Raises:
        SimulationError: If the version is unknown.
    """
    operation = _operation("app.services.simulator.parity", "get_parity_envelope")
    return cast("Mapping[str, object]", operation(version))


def get_parity_maturity_ladder() -> tuple[Mapping[str, object], ...]:
    """Return the published L1 through L5-MT5-Operational maturity ladder."""
    operation = _operation(
        "app.services.simulator.parity", "get_parity_maturity_ladder"
    )
    return cast("tuple[Mapping[str, object], ...]", operation())


def normalize_parity_evidence(
    evidence: Mapping[str, object], envelope: Mapping[str, object]
) -> dict[str, object]:
    """Normalize one side's parity evidence under a published envelope.

    Args:
        evidence: JSON-safe evidence mapping for one route execution.
        envelope: Envelope mapping from ``get_parity_envelope``.

    Returns:
        Normalized evidence mapping with the alpha-renamed relationship
        graph, causal edges, ambiguous same-timestamp groups, identifier
        map, and canonical digest.

    Raises:
        SimulationError: On malformed evidence, scope mismatch, or a broken
            identifier reference.
    """
    operation = _operation("app.services.simulator.parity", "normalize_parity_evidence")
    return cast("dict[str, object]", operation(evidence, envelope))


def compare_parity_evidence(
    left: Mapping[str, object],
    right: Mapping[str, object],
    envelope: Mapping[str, object],
) -> Mapping[str, object]:
    """Compare left and right route evidence under one published envelope.

    Args:
        left: JSON-safe evidence mapping for the simulated route execution.
        right: JSON-safe evidence mapping for the paired provider execution.
        envelope: Envelope mapping from ``get_parity_envelope``.

    Returns:
        Read-only comparison mapping with pass flag, certificate
        scope/version, per-invariant results, relationship map, aggregate
        economic error, and deterministic ordered failures.

    Raises:
        SimulationError: On malformed evidence, envelope scope violation, or
            a broken identifier reference.
    """
    operation = _operation("app.services.simulator.parity", "compare_parity_evidence")
    return cast("Mapping[str, object]", operation(left, right, envelope))


def get_same_tick_priority() -> tuple[str, ...]:
    """Return the deterministic same-tick execution priority."""
    from app.services.simulator.execution import SAME_TICK_PRIORITY

    return SAME_TICK_PRIORITY


def get_simulation_error_catalog() -> Mapping[str, object]:
    """Return the immutable Simulation error catalogue."""
    from app.services.simulator.errors import SIM_ERROR_CATALOG

    return SIM_ERROR_CATALOG


def get_simulation_migrations() -> tuple[object, ...]:
    """Return the immutable Simulation-owned migration manifest."""
    from app.services.simulator.state import SIMULATION_MIGRATIONS

    return SIMULATION_MIGRATIONS


def run_simulator_migrations(request_id: str) -> object:
    """Apply the complete immutable Simulator migration manifest through Data.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned standard migration response.
    """
    operation = _operation(
        "app.services.simulator.migrations", "run_simulator_migrations"
    )
    return operation(request_id)


def get_supported_asset_classes() -> tuple[str, ...]:
    """Return the supported Simulation asset classes."""
    from app.services.simulator.validation import SUPPORTED_ASSET_CLASSES

    return SUPPORTED_ASSET_CLASSES


def get_supported_fill_policies() -> tuple[str, ...]:
    """Return the supported deterministic fill policies."""
    from app.services.simulator.execution import SUPPORTED_FILL_POLICIES

    return SUPPORTED_FILL_POLICIES


def build_transaction_posting(**fields: object) -> object:
    """Build one immutable signed account-currency posting."""
    return _operation("app.services.simulator.accounting", "build_transaction_posting")(
        **fields
    )


def create_transaction_ledger(initial_balance: object, account_currency: str) -> object:
    """Create one opaque conserved transaction ledger."""
    return _operation("app.services.simulator.accounting", "create_transaction_ledger")(
        initial_balance, account_currency
    )


def post_transaction(ledger: object, posting: object) -> dict[str, object]:
    """Atomically apply one transaction posting."""
    return _operation("app.services.simulator.accounting", "post_transaction")(
        ledger, posting
    )  # type: ignore[return-value]


def serialize_transaction_ledger(ledger: object) -> dict[str, object]:
    """Serialize complete transaction-ledger state."""
    return _operation(
        "app.services.simulator.accounting", "serialize_transaction_ledger"
    )(ledger)  # type: ignore[return-value]


def restore_transaction_ledger(state: dict[str, object]) -> object:
    """Restore complete transaction-ledger state."""
    return _operation(
        "app.services.simulator.accounting", "restore_transaction_ledger"
    )(state)


def calculate_rollover_swap(**fields: object) -> dict[str, object]:
    """Calculate one evidence-bound server rollover swap effect."""
    return _operation("app.services.simulator.accounting", "calculate_swap_rollover")(
        **fields
    )  # type: ignore[return-value]


def schedule_simulation_rollover(*args: object, **kwargs: object) -> object:
    """Schedule the next broker-server rollover instant."""
    return _operation("app.services.simulator.accounting", "schedule_rollover")(
        *args, **kwargs
    )


def create_simulation_scheduler(*args: object, **kwargs: object) -> object:
    """Create one opaque deterministic execution scheduler."""
    return _operation("app.services.simulator.scheduler", "create_scheduler")(
        *args, **kwargs
    )


def schedule_simulation_event(*args: object, **kwargs: object) -> str:
    """Schedule one deterministic event and return its identity."""
    return cast(
        "str",
        _operation("app.services.simulator.scheduler", "schedule_event")(
            *args, **kwargs
        ),
    )


def cancel_simulation_event(*args: object, **kwargs: object) -> bool:
    """Cancel one pending deterministic event."""
    return cast(
        "bool",
        _operation("app.services.simulator.scheduler", "cancel_event")(*args, **kwargs),
    )


def get_simulation_scheduler_state(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Return bounded detached scheduler state."""
    return cast(
        "Mapping[str, object]",
        _operation("app.services.simulator.scheduler", "get_scheduler_state")(
            *args, **kwargs
        ),
    )


async def pump_simulation_scheduler_once(*args: object, **kwargs: object) -> str:
    """Pump one deterministic scheduler event."""
    operation = cast(
        "Callable[..., Awaitable[str]]",
        _operation("app.services.simulator.scheduler", "pump_scheduler_once"),
    )
    return await operation(*args, **kwargs)


async def run_simulation_scheduler_until_complete(
    *args: object, **kwargs: object
) -> object:
    """Pump deterministically until one selected event resolves."""
    operation = cast(
        "Callable[..., Awaitable[object]]",
        _operation("app.services.simulator.scheduler", "run_scheduler_until_complete"),
    )
    return await operation(*args, **kwargs)


def serialize_simulation_scheduler(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Serialize deterministic scheduler state without runtime objects."""
    return cast(
        "Mapping[str, object]",
        _operation("app.services.simulator.scheduler", "serialize_scheduler")(
            *args, **kwargs
        ),
    )


def restore_simulation_scheduler(*args: object, **kwargs: object) -> object:
    """Restore scheduler state with an explicit handler registry."""
    return _operation("app.services.simulator.scheduler", "restore_scheduler")(
        *args, **kwargs
    )


def shutdown_simulation_scheduler(*args: object, **kwargs: object) -> None:
    """Shut down one deterministic scheduler."""
    _operation("app.services.simulator.scheduler", "shutdown_scheduler")(
        *args, **kwargs
    )


def build_artifact_manifest(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Build a verified canonical artifact manifest."""
    return _guarded(
        _operation("app.services.simulator.reporting", "build_artifact_manifest"),
        operation="simulation.reporting.build_artifact_manifest",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def attach_analytics_report_artifact(
    run_id: str,
    report_json: str,
    *,
    request_id: str,
) -> StandardResponse[object]:
    """Attach one immutable Analytics report artifact to a completed run.

    Args:
        run_id: Completed canonical Simulation run identity.
        report_json: Serialized Analytics performance report JSON text.
        request_id: Trace identifier for the attachment operation.

    Returns:
        Attachment projection with artifact reference, checksum, and size.

    Raises:
        SimulationError: If the run is unknown, the payload is invalid, or a
            different report is already attached.
    """
    return _guarded(
        _operation(
            "app.services.simulator.reporting.artifacts",
            "attach_analytics_report_artifact",
        ),
        operation="simulation.reporting.attach_analytics_report_artifact",
        risk_level="medium",
        read_only=False,
        writes_file=True,
    )(run_id, report_json, request_id=request_id)


def build_json_report(*args: object, **kwargs: object) -> StandardResponse[str]:
    """Build a deterministic canonical JSON report."""
    return cast(
        "StandardResponse[str]",
        _guarded(
            _operation("app.services.simulator.reporting", "build_json_report"),
            operation="simulation.reporting.build_json_report",
            risk_level="low",
            read_only=True,
        )(*args, **kwargs),
    )


def build_markdown_report(*args: object, **kwargs: object) -> StandardResponse[str]:
    """Build a deterministic canonical Markdown report."""
    return cast(
        "StandardResponse[str]",
        _guarded(
            _operation("app.services.simulator.reporting", "build_markdown_report"),
            operation="simulation.reporting.build_markdown_report",
            risk_level="low",
            read_only=True,
        )(*args, **kwargs),
    )


def build_tick_timeline(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Build the canonical deterministic tick timeline."""
    return _guarded(
        _operation("app.services.simulator.timeline", "build_tick_timeline"),
        operation="simulation.timeline.build_tick_timeline",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def calculate_execution_costs(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Calculate configured execution costs."""
    return _guarded(
        _operation("app.services.simulator.accounting", "calculate_execution_costs"),
        operation="simulation.accounting.calculate_execution_costs",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def calculate_margin(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Calculate fixed-precision margin."""
    return _guarded(
        _operation("app.services.simulator.accounting", "calculate_margin"),
        operation="simulation.accounting.calculate_margin",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def calculate_fx_profit(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Calculate effective-dated exact FX profit."""
    return _guarded(
        _operation("app.services.simulator.calculations", "calculate_fx_profit"),
        operation="simulation.calculations.calculate_fx_profit",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def calculate_planned_margin(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Calculate effective-dated incremental planned margin."""
    return _guarded(
        _operation("app.services.simulator.calculations", "calculate_planned_margin"),
        operation="simulation.calculations.calculate_planned_margin",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def calculate_total_margin(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Calculate effective-dated total margin."""
    return _guarded(
        _operation("app.services.simulator.calculations", "calculate_total_margin"),
        operation="simulation.calculations.calculate_total_margin",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def convert_account_currency(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Convert and round one amount with Data-owned FX evidence."""
    return _guarded(
        _operation("app.services.simulator.calculations", "convert_account_currency"),
        operation="simulation.calculations.convert_account_currency",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def load_calculation_conformance_artifact(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Load one checksummed offline calculation artifact."""
    return _guarded(
        _operation(
            "app.services.simulator.calculations",
            "load_calculation_conformance_artifact",
        ),
        operation="simulation.calculations.load_conformance_artifact",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def run_offline_calculation_conformance(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Run exact provider-disabled calculation conformance."""
    return _guarded(
        _operation(
            "app.services.simulator.calculations",
            "run_offline_calculation_conformance",
        ),
        operation="simulation.calculations.run_offline_conformance",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def get_calculation_model_identity() -> StandardResponse[object]:
    """Return stable calculation model identity."""
    return _guarded(
        _operation(
            "app.services.simulator.calculations", "get_calculation_model_identity"
        ),
        operation="simulation.calculations.get_model_identity",
        risk_level="none",
        read_only=True,
    )()


def get_supported_calculation_modes() -> StandardResponse[object]:
    """Return exact admitted calculation modes."""
    return _guarded(
        _operation(
            "app.services.simulator.calculations", "get_supported_calculation_modes"
        ),
        operation="simulation.calculations.get_supported_modes",
        risk_level="none",
        read_only=True,
    )()


def convert_fx_amount(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Convert an amount using verified Data-owned FX evidence."""
    return _guarded(
        _operation("app.services.simulator.accounting", "convert_fx_amount"),
        operation="simulation.accounting.convert_fx_amount",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def evaluate_protective_exit(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Evaluate deterministic protective-exit evidence."""
    return _guarded(
        _operation("app.services.simulator.execution", "evaluate_protective_exit"),
        operation="simulation.execution.evaluate_protective_exit",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def match_order(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Match one approved order against one canonical tick."""
    return _guarded(
        _operation("app.services.simulator.execution", "match_order"),
        operation="simulation.execution.match_order",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def normalize_volume(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Normalize volume against verified symbol constraints."""
    return _guarded(
        _operation("app.services.simulator.accounting", "normalize_volume"),
        operation="simulation.accounting.normalize_volume",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def price_order(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Price one approved order against one canonical tick."""
    return _guarded(
        _operation("app.services.simulator.execution", "price_order"),
        operation="simulation.execution.price_order",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def replay_journal(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Replay and verify one canonical Simulation journal."""
    return _guarded(
        _operation("app.services.simulator.journal", "replay_journal"),
        operation="simulation.journal.replay_journal",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def resolve_idempotent_run(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Resolve one idempotent Simulation request."""
    return _guarded(
        _operation("app.services.simulator.journal", "resolve_idempotent_run"),
        operation="simulation.journal.resolve_idempotent_run",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def build_evaluation_latency(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Build scheduler-clock evaluation latency when both edges exist."""
    return _guarded(
        _operation("app.services.simulator.run", "build_evaluation_latency"),
        operation="simulation.run.build_evaluation_latency",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def build_point_in_time_dataset(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Build one Data contract bounded by a scheduler decision instant."""
    return _guarded(
        _operation("app.services.simulator.run", "build_point_in_time_dataset"),
        operation="simulation.run.build_point_in_time_dataset",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def get_margin_state(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Classify the effective provider margin-call and stop-out state."""
    return _guarded(
        _operation("app.services.simulator.accounting", "get_margin_state"),
        operation="simulation.accounting.get_margin_state",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def plan_stop_out_liquidation(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Plan one target-evidenced deterministic stop-out sequence."""
    return _guarded(
        _operation("app.services.simulator.accounting", "plan_stop_out_liquidation"),
        operation="simulation.accounting.plan_stop_out_liquidation",
        risk_level="high",
        read_only=True,
    )(*args, **kwargs)


def project_account_mode(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Project one netting or hedging position transition."""
    return _guarded(
        _operation("app.services.simulator.accounting", "project_account_mode"),
        operation="simulation.accounting.project_account_mode",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def is_provider_session_open(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Evaluate weekly and dated provider-session evidence."""
    return _guarded(
        _operation("app.services.simulator.execution", "is_provider_session_open"),
        operation="simulation.execution.is_provider_session_open",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def validate_provider_order(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Validate an order against its effective provider revision."""
    return _guarded(
        _operation("app.services.simulator.execution", "validate_provider_order"),
        operation="simulation.execution.validate_provider_order",
        risk_level="high",
        read_only=True,
    )(*args, **kwargs)


def build_lifecycle_deal(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Build one deterministic order/position-linked authority deal."""
    return _guarded(
        _operation("app.services.simulator.execution", "build_lifecycle_deal"),
        operation="simulation.execution.build_lifecycle_deal",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def build_protection_projection(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Build internal-only protection and OCO lifecycle evidence."""
    return _guarded(
        _operation("app.services.simulator.execution", "build_protection_projection"),
        operation="simulation.execution.build_protection_projection",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def describe_lifecycle_race(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Describe an evidenced lifecycle causal edge or concurrency relation."""
    return _guarded(
        _operation("app.services.simulator.execution", "describe_lifecycle_race"),
        operation="simulation.execution.describe_lifecycle_race",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def deterministic_lifecycle_ticket(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Derive one deterministic lifecycle ticket from canonical evidence."""
    return _guarded(
        _operation(
            "app.services.simulator.execution", "deterministic_lifecycle_ticket"
        ),
        operation="simulation.execution.deterministic_lifecycle_ticket",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def resolve_fill_remainder(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Resolve FOK, IOC, RETURN, or BOC lifecycle quantities."""
    return _guarded(
        _operation("app.services.simulator.execution", "resolve_fill_remainder"),
        operation="simulation.execution.resolve_fill_remainder",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def resolve_order_expiration(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Resolve one evidenced provider time-policy expiration."""
    return _guarded(
        _operation("app.services.simulator.execution", "resolve_order_expiration"),
        operation="simulation.execution.resolve_order_expiration",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


async def run_backtest_async(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Run one governed canonical Simulation backtest asynchronously."""
    operation = cast(
        "Callable[..., Awaitable[object]]",
        _operation("app.services.simulator.run", "run_backtest_async"),
    )
    return await _guarded_async(
        operation,
        operation="simulation.run.run_backtest_async",
        risk_level="medium",
        read_only=False,
        writes_file=True,
    )(*args, **kwargs)


def run_fast_research(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Run one explicitly non-canonical fast-research simulation."""
    return _guarded(
        _operation("app.services.simulator.run", "run_fast_research"),
        operation="simulation.run.run_fast_research",
        risk_level="medium",
        read_only=False,
        modifies_database=True,
    )(*args, **kwargs)


async def run_portfolio_backtest(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Run one governed portfolio simulation."""
    operation = cast(
        "Callable[..., Awaitable[object]]",
        _operation("app.services.simulator.run", "run_portfolio_backtest"),
    )
    return await _guarded_async(
        operation,
        operation="simulation.run.run_portfolio_backtest",
        risk_level="high",
        read_only=False,
        writes_file=True,
        modifies_database=True,
    )(*args, **kwargs)


def to_simulation_error_payload(error: Exception) -> Mapping[str, object]:
    """Return a bounded public Simulation error payload."""
    function = _operation(
        "app.services.simulator.errors", "to_simulation_error_payload"
    )
    return cast("Mapping[str, object]", function(error))


def unwrap_simulation_response[T](
    response: StandardResponse[T], *, operation: str
) -> T:
    """Return raw successful Simulation data or raise its controlled failure."""
    function = _operation("app.services.simulator.errors", "unwrap_simulation_response")
    return cast("T", function(response, operation=operation))


def validate_fx_evidence(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Validate Data-owned FX conversion evidence."""
    return _guarded(
        _operation("app.services.simulator.accounting", "validate_fx_evidence"),
        operation="simulation.accounting.validate_fx_evidence",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def validate_intent_timing(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Validate no-lookahead intent timing."""
    return _guarded(
        _operation("app.services.simulator.timeline", "validate_intent_timing"),
        operation="simulation.timeline.validate_intent_timing",
        risk_level="medium",
        read_only=True,
    )(*args, **kwargs)


def validate_market_data(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Validate execution-critical Data-owned market evidence."""
    return _guarded(
        _operation("app.services.simulator.validation", "validate_market_data"),
        operation="simulation.validation.validate_market_data",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def validate_market_evidence_lineage(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Validate independent source/tick lineage and decision-time eligibility."""
    return _guarded(
        _operation(
            "app.services.simulator.validation", "validate_market_evidence_lineage"
        ),
        operation="simulation.validation.validate_market_evidence_lineage",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def validate_phase_one_scope(
    *args: object, **kwargs: object
) -> StandardResponse[object]:
    """Validate the approved Phase 1 Simulation scope."""
    return _guarded(
        _operation("app.services.simulator.validation", "validate_phase_one_scope"),
        operation="simulation.validation.validate_phase_one_scope",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def validate_run_inputs(*args: object, **kwargs: object) -> StandardResponse[object]:
    """Validate one governed Simulation request and reference set."""
    return _guarded(
        _operation("app.services.simulator.validation", "validate_run_inputs"),
        operation="simulation.validation.validate_run_inputs",
        risk_level="low",
        read_only=True,
    )(*args, **kwargs)


def _call_feature(module: str, name: str, *args: object, **kwargs: object) -> Any:
    """Call one allowlisted focused feature operation."""
    return _operation(module, name)(*args, **kwargs)


def build_checklist_definition(**fields: object) -> object:
    """Build one validated Simulation checklist definition."""
    return _call_feature(
        "app.services.simulator.checklists", "build_checklist_definition", **fields
    )


def start_simulation_checklist(*args: object, **kwargs: object) -> object:
    """Start one deterministic Simulation checklist runtime."""
    return _call_feature(
        "app.services.simulator.checklists", "start_checklist", *args, **kwargs
    )


def evaluate_simulation_checklist(*args: object, **kwargs: object) -> object:
    """Evaluate checklist steps against actual-state evidence."""
    return _call_feature(
        "app.services.simulator.checklists", "evaluate_checklist", *args, **kwargs
    )


def bypass_simulation_checklist_step(*args: object, **kwargs: object) -> object:
    """Bypass one optional checklist step under mode policy."""
    return _call_feature(
        "app.services.simulator.checklists",
        "bypass_checklist_step",
        *args,
        **kwargs,
    )


def get_simulation_mode_policy(mode: str) -> Mapping[str, object]:
    """Return immutable assistance and route policy for one mode."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.checklists", "get_simulation_mode_policy", mode
        ),
    )


def complete_simulation_mission(*args: object, **kwargs: object) -> object:
    """Resolve one checklist-bound simulation mission outcome."""
    return _call_feature(
        "app.services.simulator.checklists",
        "complete_simulation_mission",
        *args,
        **kwargs,
    )


def build_mission_definition(**fields: object) -> object:
    """Build one validated Simulator-owned mission definition."""
    return _call_feature(
        "app.services.simulator.scenarios", "build_mission_definition", **fields
    )


def build_injected_event(**fields: object) -> object:
    """Build one validated injected scenario event."""
    return _call_feature(
        "app.services.simulator.scenarios", "build_injected_event", **fields
    )


def evaluate_scenario_triggers(*args: object, **kwargs: object) -> tuple[str, ...]:
    """Evaluate deterministic scenario triggers."""
    return cast(
        "tuple[str, ...]",
        _call_feature(
            "app.services.simulator.scenarios",
            "evaluate_scenario_triggers",
            *args,
            **kwargs,
        ),
    )


def order_injected_events(*args: object, **kwargs: object) -> tuple[object, ...]:
    """Return totally ordered compatible injected events."""
    return cast(
        "tuple[object, ...]",
        _call_feature(
            "app.services.simulator.scenarios",
            "order_injected_events",
            *args,
            **kwargs,
        ),
    )


def get_scenario_templates() -> Mapping[str, object]:
    """Return supported emergency and abnormal scenario templates."""
    return cast(
        "Mapping[str, object]",
        _call_feature("app.services.simulator.scenarios", "get_scenario_templates"),
    )


def build_scenario_provider(*args: object, **kwargs: object) -> object:
    """Build an opaque Optimization scenario provider."""
    return _call_feature(
        "app.services.simulator.scenarios", "build_scenario_provider", *args, **kwargs
    )


def build_scenario_evidence_provider(
    *args: object, **kwargs: object
) -> Callable[[str], Mapping[str, object] | None]:
    """Build a callable Research scenario-evidence provider."""
    return cast(
        "Callable[[str], Mapping[str, object] | None]",
        _call_feature(
            "app.services.simulator.scenarios",
            "build_scenario_evidence_provider",
            *args,
            **kwargs,
        ),
    )


def build_latency_profile(**fields: object) -> object:
    """Build one deterministic execution latency profile."""
    return _call_feature(
        "app.services.simulator.realism", "build_latency_profile", **fields
    )


def build_queue_model(**fields: object) -> object:
    """Build one deterministic execution queue model."""
    return _call_feature(
        "app.services.simulator.realism", "build_queue_model", **fields
    )


def project_latency_timestamps(*args: object, **kwargs: object) -> Mapping[str, object]:
    """Project explicit causal timestamps across modeled latency domains."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "project_latency_timestamps",
            *args,
            **kwargs,
        ),
    )


def simulate_queue_fill(*args: object, **kwargs: object) -> object:
    """Project one deterministic price-level queue fill."""
    return _call_feature(
        "app.services.simulator.realism", "simulate_queue_fill", *args, **kwargs
    )


def price_realistic_execution(*args: object, **kwargs: object) -> object:
    """Apply bounded slippage and market impact to one base match."""
    return _call_feature(
        "app.services.simulator.realism", "price_realistic_execution", *args, **kwargs
    )


def resolve_cancel_replace_race(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Resolve one cancel, replace, and fill race."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "resolve_cancel_replace_race",
            *args,
            **kwargs,
        ),
    )


def project_execution_views(*args: object, **kwargs: object) -> Mapping[str, object]:
    """Separate venue-effective and player-perceived execution views."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "project_execution_views",
            *args,
            **kwargs,
        ),
    )


def build_fill_model_provider(*args: object, **kwargs: object) -> object:
    """Build an opaque Optimization fill-model provider."""
    return _call_feature(
        "app.services.simulator.realism", "build_fill_model_provider", *args, **kwargs
    )


def create_realism_stream(*args: object, **kwargs: object) -> object:
    """Create one pinned concern-specific deterministic stream."""
    return _call_feature(
        "app.services.simulator.realism", "create_realism_stream", *args, **kwargs
    )


def sample_realism_stream(*args: object, **kwargs: object) -> object:
    """Draw once from a deterministic realism stream."""
    return _call_feature(
        "app.services.simulator.realism", "sample_realism_stream", *args, **kwargs
    )


def serialize_realism_stream(*args: object, **kwargs: object) -> Mapping[str, object]:
    """Serialize exact realism generator identity and counter."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "serialize_realism_stream",
            *args,
            **kwargs,
        ),
    )


def restore_realism_stream(*args: object, **kwargs: object) -> object:
    """Restore one verified realism stream state."""
    return _call_feature(
        "app.services.simulator.realism", "restore_realism_stream", *args, **kwargs
    )


def get_realism_stream_identity(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Return pinned stream algorithm identity and golden vectors."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "get_realism_stream_identity",
            *args,
            **kwargs,
        ),
    )


def get_realism_performance_budgets(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Return published annual-M1 and multi-symbol realism budgets."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "get_realism_performance_budgets",
            *args,
            **kwargs,
        ),
    )


def admit_calibrated_realism(*args: object, **kwargs: object) -> object:
    """Admit one exact applicable calibration into execution realism."""
    return _call_feature(
        "app.services.simulator.realism",
        "admit_calibrated_realism",
        *args,
        **kwargs,
    )


def sample_calibrated_realism(*args: object, **kwargs: object) -> Mapping[str, object]:
    """Sample one calibrated component with journal evidence."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "sample_calibrated_realism",
            *args,
            **kwargs,
        ),
    )


def get_simulation_crash_points(*args: object, **kwargs: object) -> tuple[str, ...]:
    """Return every registered deterministic crash boundary."""
    return cast(
        "tuple[str, ...]",
        _call_feature(
            "app.services.simulator.realism",
            "get_simulation_crash_points",
            *args,
            **kwargs,
        ),
    )


def create_simulation_recovery_state(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Create one immutable unknown-outcome crash recovery state."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "create_recovery_state",
            *args,
            **kwargs,
        ),
    )


def recover_simulation_unknown_outcome(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Converge by authority query without repeating an uncertain mutation."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.realism",
            "recover_unknown_outcome",
            *args,
            **kwargs,
        ),
    )


def bind_realism_stream_to_scheduler(*args: object, **kwargs: object) -> None:
    """Bind one realism stream into exact scheduler checkpoint state."""
    _call_feature(
        "app.services.simulator.scheduler", "bind_realism_stream", *args, **kwargs
    )


def schedule_calibrated_realism_event(*args: object, **kwargs: object) -> str:
    """Schedule one admitted calibrated sample deterministically."""
    return cast(
        "str",
        _call_feature(
            "app.services.simulator.scheduler",
            "schedule_calibrated_realism_event",
            *args,
            **kwargs,
        ),
    )


def build_seeded_fault_event(*args: object, **kwargs: object) -> object:
    """Create a deterministic calibrated fault through the scenario engine."""
    return _call_feature(
        "app.services.simulator.scenarios", "build_seeded_fault_event", *args, **kwargs
    )


def partition_calibration_evidence(*args: object, **kwargs: object) -> object:
    """Partition eligible execution evidence before empirical fitting."""
    return _call_feature(
        "app.services.simulator.calibration",
        "partition_calibration_evidence",
        *args,
        **kwargs,
    )


def fit_spread_calibration(*args: object, **kwargs: object) -> object:
    """Fit one governed provider-M1 spread calibration artifact."""
    return _call_feature(
        "app.services.simulator.calibration", "fit_spread_calibration", *args, **kwargs
    )


def fit_execution_calibration(*args: object, **kwargs: object) -> object:
    """Fit sufficiently evidenced execution components."""
    return _call_feature(
        "app.services.simulator.calibration",
        "fit_execution_calibration",
        *args,
        **kwargs,
    )


def validate_calibration_artifact(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Validate calibration against its locked validation evidence."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.calibration",
            "validate_calibration_artifact",
            *args,
            **kwargs,
        ),
    )


def get_calibration_applicability(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Return artifact applicability, exclusions, and validity."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.calibration",
            "get_calibration_applicability",
            *args,
            **kwargs,
        ),
    )


def dump_calibration_artifact(*args: object, **kwargs: object) -> dict[str, object]:
    """Serialize one verified calibration artifact."""
    return cast(
        "dict[str, object]",
        _call_feature(
            "app.services.simulator.calibration",
            "dump_calibration_artifact",
            *args,
            **kwargs,
        ),
    )


def load_calibration_artifact(*args: object, **kwargs: object) -> object:
    """Load and checksum-verify one calibration artifact."""
    return _call_feature(
        "app.services.simulator.calibration",
        "load_calibration_artifact",
        *args,
        **kwargs,
    )


def build_replay_identity(**fields: object) -> object:
    """Build the canonical Simulator replay identity."""
    return _call_feature(
        "app.services.simulator.recovery", "build_replay_identity", **fields
    )


def create_recovery_checkpoint(*args: object, **kwargs: object) -> object:
    """Create one immutable hash-linked recovery checkpoint."""
    return _call_feature(
        "app.services.simulator.recovery",
        "create_recovery_checkpoint",
        *args,
        **kwargs,
    )


def verify_recovery_checkpoints(*args: object, **kwargs: object) -> bool:
    """Verify one complete recovery checkpoint chain."""
    return cast(
        "bool",
        _call_feature(
            "app.services.simulator.recovery",
            "verify_recovery_checkpoints",
            *args,
            **kwargs,
        ),
    )


def branch_recovery_checkpoint(
    *args: object, **kwargs: object
) -> tuple[object, object]:
    """Create an isolated practice recovery branch."""
    return cast(
        "tuple[object, object]",
        _call_feature(
            "app.services.simulator.recovery",
            "branch_recovery_checkpoint",
            *args,
            **kwargs,
        ),
    )


def restore_simulation_session(*args: object, **kwargs: object) -> Mapping[str, object]:
    """Restore the latest verified secured-session state."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.recovery",
            "restore_simulation_session",
            *args,
            **kwargs,
        ),
    )


def explicitly_rearm_simulation_session(
    *args: object, **kwargs: object
) -> Mapping[str, object]:
    """Explicitly rearm one verified restored session."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.recovery",
            "explicitly_rearm_simulation_session",
            *args,
            **kwargs,
        ),
    )


def secure_simulation_session(*args: object, **kwargs: object) -> Mapping[str, object]:
    """Secure one durable session for governed recovery."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.recovery",
            "secure_simulation_session",
            *args,
            **kwargs,
        ),
    )


def persist_recovery_checkpoint(*args: object, **kwargs: object) -> None:
    """Persist one immutable recovery checkpoint."""
    _call_feature(
        "app.services.simulator.recovery",
        "persist_recovery_checkpoint",
        *args,
        **kwargs,
    )


def load_recovery_checkpoints(*args: object, **kwargs: object) -> tuple[object, ...]:
    """Load one secured session's ordered checkpoints."""
    return cast(
        "tuple[object, ...]",
        _call_feature(
            "app.services.simulator.recovery",
            "load_recovery_checkpoints",
            *args,
            **kwargs,
        ),
    )


def persist_recovery_state(*args: object, **kwargs: object) -> None:
    """Persist one secured session recovery projection."""
    _call_feature(
        "app.services.simulator.recovery", "persist_recovery_state", *args, **kwargs
    )


def build_simulation_alert(**fields: object) -> object:
    """Build one immutable simulated-session alert."""
    return _call_feature(
        "app.services.simulator.alerts", "build_simulation_alert", **fields
    )


def transition_simulation_alert(*args: object, **kwargs: object) -> object:
    """Apply one declared latched alert transition."""
    return _call_feature(
        "app.services.simulator.alerts",
        "transition_simulation_alert",
        *args,
        **kwargs,
    )


def group_simulation_alerts(*args: object, **kwargs: object) -> Mapping[str, object]:
    """Group simulated alerts by deterministic root cause."""
    return cast(
        "Mapping[str, object]",
        _call_feature(
            "app.services.simulator.alerts",
            "group_simulation_alerts",
            *args,
            **kwargs,
        ),
    )


def evaluate_emergency_controls(*args: object, **kwargs: object) -> Mapping[str, bool]:
    """Evaluate fail-closed emergency-control availability."""
    return cast(
        "Mapping[str, bool]",
        _call_feature(
            "app.services.simulator.alerts",
            "evaluate_emergency_controls",
            *args,
            **kwargs,
        ),
    )


__all__: tuple[str, ...] = (
    "admit_calibrated_realism",
    "attach_analytics_report_artifact",
    "bind_realism_stream_to_scheduler",
    "branch_live_simulation",
    "branch_recovery_checkpoint",
    "build_artifact_manifest",
    "build_backtest_job_registry",
    "build_checklist_definition",
    "build_evaluation_latency",
    "build_fill_model_provider",
    "build_injected_event",
    "build_json_report",
    "build_latency_profile",
    "build_lifecycle_deal",
    "build_markdown_report",
    "build_mission_definition",
    "build_point_in_time_dataset",
    "build_protection_projection",
    "build_queue_model",
    "build_replay_identity",
    "build_scenario_evidence_provider",
    "build_scenario_provider",
    "build_seeded_fault_event",
    "build_simulation_alert",
    "build_simulation_run_dependencies",
    "build_simulation_state_store",
    "build_tick_timeline",
    "build_transaction_posting",
    "bypass_simulation_checklist_step",
    "calculate_execution_costs",
    "calculate_fast_research_config_hash",
    "calculate_fx_profit",
    "calculate_margin",
    "calculate_planned_margin",
    "calculate_portfolio_backtest_config_hash",
    "calculate_rollover_swap",
    "calculate_simulation_backtest_config_hash",
    "calculate_total_margin",
    "cancel_simulation_event",
    "close_live_simulation_session",
    "compare_parity_evidence",
    "complete_simulation_mission",
    "convert_account_currency",
    "convert_fx_amount",
    "create_backtest_provider_facts",
    "create_backtest_run_config",
    "create_live_simulation_session",
    "create_realism_stream",
    "create_recovery_checkpoint",
    "create_simulation_handle",
    "create_simulation_recovery_state",
    "create_simulation_scheduler",
    "create_simulation_session",
    "create_simulation_value",
    "create_transaction_ledger",
    "describe_lifecycle_race",
    "deterministic_lifecycle_ticket",
    "dump_calibration_artifact",
    "dump_simulation_value",
    "evaluate_emergency_controls",
    "evaluate_protective_exit",
    "evaluate_scenario_triggers",
    "evaluate_simulation_checklist",
    "execute_backtest_job_inspection",
    "execute_backtest_job_operation",
    "execute_live_simulation_command",
    "execute_simulation_handle_operation",
    "execute_simulation_state_store_operation",
    "explicitly_rearm_simulation_session",
    "finalize_live_simulation_session",
    "fit_execution_calibration",
    "fit_spread_calibration",
    "get_approved_tick_models",
    "get_backtest_strategy_catalogue",
    "get_calculation_model_identity",
    "get_calibration_applicability",
    "get_canonical_artifact_types",
    "get_journal_policy",
    "get_margin_state",
    "get_parity_envelope",
    "get_parity_maturity_ladder",
    "get_realism_performance_budgets",
    "get_realism_stream_identity",
    "get_report_schema_version",
    "get_same_tick_priority",
    "get_scenario_templates",
    "get_simulation_crash_points",
    "get_simulation_error_catalog",
    "get_simulation_migrations",
    "get_simulation_mode_policy",
    "get_simulation_result",
    "get_simulation_scheduler_state",
    "get_simulation_value_field",
    "get_simulation_value_fields",
    "get_supported_asset_classes",
    "get_supported_calculation_modes",
    "get_supported_fill_policies",
    "group_simulation_alerts",
    "is_provider_session_open",
    "is_simulation_value",
    "list_live_simulation_sessions",
    "load_calculation_conformance_artifact",
    "load_calibration_artifact",
    "load_recovery_checkpoints",
    "match_order",
    "normalize_parity_evidence",
    "normalize_volume",
    "order_injected_events",
    "partition_calibration_evidence",
    "persist_recovery_checkpoint",
    "persist_recovery_state",
    "plan_stop_out_liquidation",
    "post_transaction",
    "price_order",
    "price_realistic_execution",
    "project_account_mode",
    "project_execution_views",
    "project_latency_timestamps",
    "pump_simulation_scheduler_once",
    "read_live_simulation_state",
    "read_live_simulation_viewport",
    "read_simulation_session",
    "rearm_live_simulation_session",
    "recover_simulation_unknown_outcome",
    "replay_journal",
    "reset_live_simulation_sessions",
    "resolve_cancel_replace_race",
    "resolve_fill_remainder",
    "resolve_idempotent_run",
    "resolve_order_expiration",
    "restore_live_simulation_session",
    "restore_realism_stream",
    "restore_simulation_scheduler",
    "restore_simulation_session",
    "restore_transaction_ledger",
    "run_backtest_async",
    "run_fast_research",
    "run_offline_calculation_conformance",
    "run_portfolio_backtest",
    "run_simulation_scheduler_until_complete",
    "run_simulator_migrations",
    "sample_calibrated_realism",
    "sample_realism_stream",
    "schedule_calibrated_realism_event",
    "schedule_simulation_event",
    "schedule_simulation_rollover",
    "secure_simulation_session",
    "seek_live_simulation",
    "serialize_realism_stream",
    "serialize_simulation_scheduler",
    "serialize_transaction_ledger",
    "shutdown_simulation_scheduler",
    "simulate_queue_fill",
    "start_simulation_checklist",
    "step_live_simulation",
    "stream_simulation_session_frames",
    "submit_live_simulation_order",
    "to_simulation_error_payload",
    "transition_simulation_alert",
    "unwrap_simulation_response",
    "validate_calibration_artifact",
    "validate_fx_evidence",
    "validate_intent_timing",
    "validate_market_data",
    "validate_market_evidence_lineage",
    "validate_phase_one_scope",
    "validate_provider_order",
    "validate_run_inputs",
    "verify_recovery_checkpoints",
)
