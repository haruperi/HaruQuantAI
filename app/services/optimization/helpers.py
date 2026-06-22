"""Optimization Service helpers and backtest adapters.

Provides execution helpers, dynamic strategy loading, parameter space
hashing, JSON-safe serialization contracts, and shared result utilities.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import math
import random as _random_module
import sys
import warnings
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from app.utils.errors import Error
from app.utils.standard import StandardResponse, canonical_json

if TYPE_CHECKING:
    from app.services.optimization.models import (
        OptimizationResult,
        ParameterCandidate,
        ParameterSpace,
    )

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------
Infinity = float("inf")
OPT_JSON_SERIALIZATION_FAILED = "OPT_JSON_SERIALIZATION_FAILED"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class OptimizationExecutionError(Error):
    """Execution error within the optimization service."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
    ) -> None:
        """Initialize optimization execution error.

        Args:
            message: Human-readable error description.
            code: Optional structured error code (default
                ``OPT_EXECUTION_FAILED``).
        """
        super().__init__(message)
        self.code = code or "OPT_EXECUTION_FAILED"


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class EngineOptimizationResult:
    """Optimization-ready result contract built from engine outputs.

    Attributes:
        run_id: Unique backtest run identifier.
        ending_balance: Final account balance.
        net_profit: Net profit (ending minus initial balance).
        total_trades: Number of closed round-trip trades.
        trades: List of realized trade dictionaries.
        processed_ticks: Total tick/bar count processed.
        analytics: Summary metric dictionary from the engine.
        success: True when execution completed without error.
    """

    run_id: str
    ending_balance: float
    net_profit: float
    total_trades: int
    trades: list[dict[str, Any]]
    processed_ticks: int
    analytics: dict[str, Any]
    success: bool


# ---------------------------------------------------------------------------
# Strategy identity helpers
# ---------------------------------------------------------------------------
def strategy_id(strategy: Any) -> str:  # noqa: ANN401
    """Return the deterministic strategy identifier.

    Args:
        strategy: Strategy class, instance, or identifier string.

    Returns:
        str: Deterministic strategy identifier string.
    """
    if isinstance(strategy, type):
        return str(strategy.__name__)
    if hasattr(strategy, "strategy_ref"):
        return str(strategy.strategy_ref)
    if hasattr(strategy, "__name__"):
        return str(strategy.__name__)
    return str(type(strategy).__name__)


def normalize_engine_type(engine_type: str) -> str:
    """Normalize legacy engine labels to supported execution engine names.

    Args:
        engine_type: Candidate engine label string.

    Returns:
        str: Canonical engine name.
    """
    if not engine_type:
        return "event_driven"
    val = engine_type.strip().lower()
    if val in ("legacy", "event_driven", "eventdriven", "event-driven"):
        return "event_driven"
    return val


# ---------------------------------------------------------------------------
# Dynamic strategy loading
# ---------------------------------------------------------------------------
def load_strategy_from_path(file_path: str, class_name: str) -> type:
    """Load a strategy class from a Python file dynamically.

    Args:
        file_path: Path to the Python source file.
        class_name: Name of the target class to load.

    Returns:
        type: Loaded strategy class object.

    Raises:
        OptimizationExecutionError: If the file is missing, the module
            spec cannot be built, or the class cannot be loaded.
    """
    path = Path(file_path)
    if not path.exists():
        msg = f"Strategy file not found: {file_path}"
        raise OptimizationExecutionError(
            msg,
            code="OPT_STRATEGY_LOAD_FAILED",
        )

    module_name = f"dynamic_strategy_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise OptimizationExecutionError(
            "Could not build module spec.",
            code="OPT_STRATEGY_LOAD_FAILED",
        )

    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return cast("type", getattr(module, class_name))
    except Exception as exc:
        msg = f"Failed to load strategy class '{class_name}': {exc}"
        raise OptimizationExecutionError(
            msg,
            code="OPT_STRATEGY_LOAD_FAILED",
        ) from exc


# ---------------------------------------------------------------------------
# Backtest execution helpers
# ---------------------------------------------------------------------------
def run_strategy_backtest(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameters: dict[str, Any],
    initial_balance: float = 10000.0,
    engine_type: str = "event_driven",
    **kwargs: Any,  # noqa: ANN401
) -> EngineOptimizationResult:
    """Run one optimization candidate through the backtest engine.

    Args:
        strategy_ref: Strategy name reference.
        symbols: Target symbol list.
        timeframe: Bar timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameters: Strategy configuration parameters.
        initial_balance: Starting cash balance.
        engine_type: Engine implementation label.
        **kwargs: Additional adapter options including:
            ``adapter_version`` (str, default ``"0.8.0"``),
            ``stochastic_realism`` (bool),
            ``deterministic_only`` (bool),
            ``request_id`` (str),
            ``actor_context`` (dict),
            ``metadata`` (dict).

    Returns:
        EngineOptimizationResult: Converted backtest metrics.

    Raises:
        OptimizationExecutionError: If validation or execution fails.
    """
    if not strategy_ref:
        raise OptimizationExecutionError(
            "strategy_ref is required.",
            code="OPT_STRATEGY_LOAD_FAILED",
        )
    if not symbols:
        raise OptimizationExecutionError(
            "symbols cannot be empty.",
            code="OPT_SYMBOL_SETUP_FAILED",
        )

    normalized_engine = normalize_engine_type(engine_type)
    if normalized_engine != "event_driven":
        msg = f"Unsupported engine type: {engine_type}"
        raise OptimizationExecutionError(msg, code="OPT_ENGINE_CREATION_FAILED")

    adapter_version = kwargs.get("adapter_version", "0.8.0")
    if adapter_version != "0.8.0":
        raise OptimizationExecutionError(
            "Backtest adapter version mismatch.",
            code="OPT_CANDIDATE_EXECUTION_FAILED",
        )

    if (
        kwargs.get("stochastic_realism") is True
        and kwargs.get("deterministic_only") is True
    ):
        raise OptimizationExecutionError(
            "Stochastic realism is active in deterministic-only mode.",
            code="OPT_NOISY_OBJECTIVE_NOT_ALLOWED",
        )

    from app.services.simulator.engine import (  # type: ignore[import-not-found, unused-ignore]
        EventDrivenExecutionEngine,
    )
    from app.services.simulator.orchestrator import (  # type: ignore[import-not-found, unused-ignore]
        BacktestOrchestrator,
    )

    engine = EventDrivenExecutionEngine()
    orchestrator = BacktestOrchestrator(engine=engine)

    payload = {
        "request_id": kwargs.get("request_id") or "opt_req_123",
        "actor_context": kwargs.get("actor_context")
        or {
            "actor_id": "optimization-service",
            "roles": ["researcher"],
        },
        "strategy_ref": strategy_ref,
        "symbols": symbols,
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "strategy_config": parameters,
        "initial_balance": initial_balance,
        "metadata": kwargs.get("metadata") or {},
    }

    try:
        response = orchestrator.execute(payload)
    except Exception as exc:
        msg = f"Candidate execution failed: {exc}"
        raise OptimizationExecutionError(
            msg, code="OPT_CANDIDATE_EXECUTION_FAILED"
        ) from exc

    if response.get("status") == "error":
        err = response.get("error") or {}
        code = err.get("code") or "OPT_CANDIDATE_EXECUTION_FAILED"
        details = err.get("details") or response.get("message") or "Backtest run failed"
        raise OptimizationExecutionError(details, code=code)

    data = response.get("data") or {}
    run_id = data.get("run_id") or "unknown_run"
    metrics = data.get("summary_metrics") or {}

    deals_list: list[dict[str, Any]] = [
        {
            "deal_id": deal.deal_id,
            "order_id": deal.order_id,
            "symbol": deal.symbol,
            "side": str(deal.side),
            "volume": deal.volume,
            "price": deal.price,
            "commission": deal.commission,
            "margin": deal.margin,
            "executed_at": deal.executed_at,
        }
        for deal in engine.deals.values()
    ]

    realized_trades = _pair_deals_into_trades(deals_list)

    ending_balance = metrics.get("ending_balance", initial_balance)
    return EngineOptimizationResult(
        run_id=run_id,
        ending_balance=ending_balance,
        net_profit=ending_balance - initial_balance,
        total_trades=len(realized_trades),
        trades=realized_trades,
        processed_ticks=int(metrics.get("processed_ticks", 0)),
        analytics=metrics,
        success=True,
    )


def _pair_deals_into_trades(
    deals_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Pair flat deal records into round-trip closed trades.

    Args:
        deals_list: Chronologically ordered deal records.

    Returns:
        list[dict[str, Any]]: Realized round-trip trade records.
    """
    realized_trades: list[dict[str, Any]] = []
    open_buys: dict[str, list[dict[str, Any]]] = {}
    open_sells: dict[str, list[dict[str, Any]]] = {}

    for d in sorted(deals_list, key=lambda d: d["executed_at"]):
        sym = str(d["symbol"])
        side = str(d["side"])
        vol = float(d["volume"])
        price = float(d["price"])
        comm = float(d["commission"])

        if "buy" in side.lower():
            if open_sells.get(sym):
                match = open_sells[sym].pop(0)
                profit = (match["price"] - price) * vol * 100000.0 - (
                    comm + match["commission"]
                )
                realized_trades.append(
                    {
                        "symbol": sym,
                        "direction": "sell",
                        "open_price": match["price"],
                        "close_price": price,
                        "volume": vol,
                        "profit": profit,
                        "open_time": match["executed_at"],
                        "close_time": d["executed_at"],
                    }
                )
            else:
                open_buys.setdefault(sym, []).append(d)
        elif open_buys.get(sym):
            match = open_buys[sym].pop(0)
            profit = (price - match["price"]) * vol * 100000.0 - (
                comm + match["commission"]
            )
            realized_trades.append(
                {
                    "symbol": sym,
                    "direction": "buy",
                    "open_price": match["price"],
                    "close_price": price,
                    "volume": vol,
                    "profit": profit,
                    "open_time": match["executed_at"],
                    "close_time": d["executed_at"],
                }
            )
        else:
            open_sells.setdefault(sym, []).append(d)

    return realized_trades


def run_strategy_backtest_from_path(
    file_path: str,
    class_name: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameters: dict[str, Any],
    initial_balance: float = 10000.0,
    engine_type: str = "event_driven",
    **kwargs: Any,  # noqa: ANN401
) -> EngineOptimizationResult:
    """Load a strategy class from disk and run one candidate simulation.

    Args:
        file_path: Strategy source code file path.
        class_name: Class name within the module.
        symbols: Target symbol list.
        timeframe: Resolution timeframe string.
        start: Start date ISO string.
        end: End date ISO string.
        parameters: Strategy configuration dictionary.
        initial_balance: Initial cash balance.
        engine_type: Engine type label.
        **kwargs: Additional adapter keyword arguments forwarded to
            :func:`run_strategy_backtest`.

    Returns:
        EngineOptimizationResult: Simulator execution result.
    """
    strategy_class = load_strategy_from_path(file_path, class_name)
    # B010 suppressed: setting a dynamic strategy identity attribute.
    setattr(strategy_class, "strategy_id", class_name)  # noqa: B010
    from app.services.strategies.registry import (  # type: ignore[import-not-found, unused-ignore]
        register_strategy,
    )

    register_strategy(strategy_class)

    return run_strategy_backtest(
        strategy_ref=strategy_class.__name__,
        symbols=symbols,
        timeframe=timeframe,
        start=start,
        end=end,
        parameters=parameters,
        initial_balance=initial_balance,
        engine_type=engine_type,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Hashing utilities
# ---------------------------------------------------------------------------
def parameter_space_hash(parameter_space: ParameterSpace) -> str:
    """Generate a deterministic order-invariant SHA-256 hash of a space.

    The hash is order-invariant (sorts parameters by name), canonicalizes
    numeric fields to 8 decimal places, sorts option lists, and includes
    constraint expressions after canonical sorting.

    Args:
        parameter_space: The parameter space definition to hash.

    Returns:
        str: 64-character hex hash representation.
    """
    sorted_params = sorted(parameter_space.parameters, key=lambda p: p.name)
    param_list = []
    for p in sorted_params:
        p_dict = p.model_dump()
        for k in ("min_value", "max_value", "step"):
            if p_dict.get(k) is not None:
                p_dict[k] = round(float(p_dict[k]), 8)
        if p_dict.get("options") is not None:
            with contextlib.suppress(Exception):
                p_dict["options"] = sorted(p_dict["options"], key=str)
        param_list.append(p_dict)

    canonical_repr = {
        "parameters": param_list,
        "constraints": sorted(parameter_space.constraints),
    }
    return hashlib.sha256(canonical_json(canonical_repr).encode("utf-8")).hexdigest()


def get_active_parameters(
    parameters: dict[str, Any],
    space: ParameterSpace,
) -> dict[str, Any]:
    """Filter out inactive conditional parameters.

    Args:
        parameters: Candidate parameters (full set).
        space: Parameter space schema defining conditionals.

    Returns:
        dict[str, Any]: Mapping containing only active parameters.
    """
    param_map = {p.name: p for p in space.parameters}

    def is_active(name: str) -> bool:
        p = param_map.get(name)
        if not p:
            return True
        if p.conditional_on is None:
            return True
        if not is_active(p.conditional_on):
            return False
        parent_value = parameters.get(p.conditional_on)
        if p.conditional_values is None:
            return False
        return parent_value in p.conditional_values

    return {
        name: round(val, 8) if isinstance(val, float) else val
        for name, val in parameters.items()
        if is_active(name)
    }


def build_candidate_hash(
    strategy_hash: str,
    data_hash: str,
    cost_model_hash: str,
    realism_profile_hash: str,
    objective_hash: str,
    engine_type: str,
    module_version: str,
    parameters: dict[str, Any],
    space: ParameterSpace,
) -> str:
    """Deterministically generate a candidate deduplication hash.

    Inactive conditional parameters are excluded before hashing.  All
    numeric parameter values are rounded to 8 decimal places for
    canonical normalization.

    Args:
        strategy_hash: Strategy ID or code hash.
        data_hash: Market data range hash.
        cost_model_hash: Cost model configuration hash.
        realism_profile_hash: Simulator realism configuration hash.
        objective_hash: Scoring function hash.
        engine_type: Backtest engine selection type.
        module_version: Optimization package version string.
        parameters: Candidate parameter dictionary (full set).
        space: Parameter space defining active variables and constraints.

    Returns:
        str: 64-character SHA-256 deduplication hash.
    """
    active = get_active_parameters(parameters, space)
    sorted_params = {k: active[k] for k in sorted(active)}

    payload = {
        "strategy_hash": strategy_hash,
        "data_hash": data_hash,
        "cost_model_hash": cost_model_hash,
        "realism_profile_hash": realism_profile_hash,
        "objective_hash": objective_hash,
        "engine_type": engine_type.lower().strip(),
        "module_version": module_version,
        "parameters": sorted_params,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Shared candidate selection helper
# ---------------------------------------------------------------------------
def select_best_candidate(
    results: list[OptimizationResult],
) -> tuple[ParameterCandidate, float]:
    """Return the best candidate and its score from evaluated results.

    When no results are provided or all scores are ``-inf``, a sentinel
    empty candidate with score ``0.0`` is returned.

    Args:
        results: Evaluated candidate result list.

    Returns:
        tuple[ParameterCandidate, float]: Best candidate and its score.
    """
    from app.services.optimization.models import (
        ParameterCandidate,
    )

    best_score = -float("inf")
    best_cand: ParameterCandidate | None = None

    for r in results:
        if r.score > best_score:
            best_score = r.score
            best_cand = ParameterCandidate(
                parameters=r.parameters,
                candidate_hash=r.metadata.get("candidate_hash", ""),
            )

    if best_cand is None:
        return (
            ParameterCandidate(parameters={}, candidate_hash="empty"),
            0.0,
        )
    return best_cand, best_score


# ---------------------------------------------------------------------------
# JSON-safe serialization
# ---------------------------------------------------------------------------
def json_safe_serialize(obj: Any) -> Any:  # noqa: ANN401,C901,PLR0911,PLR0912
    """Serialize an object into a JSON-safe representation.

    Conversion rules:
    - ``float`` NaN / ±Infinity → ``null`` with a ``RuntimeWarning``.
    - ``datetime`` → UTC ISO-8601 string (timezone enforced).
    - ``date`` → ISO-8601 date string.
    - ``Decimal`` → normalized string via ``Decimal.normalize()``.
    - ``set`` / ``frozenset`` → sorted list (deterministic ordering).
    - ``list`` / ``tuple`` → list.
    - ``dict`` → dict with string keys.
    - Unsupported types → raises with ``OPT_JSON_SERIALIZATION_FAILED``.

    Args:
        obj: Input object to serialize.

    Returns:
        Any: JSON-safe representation of the input object.

    Raises:
        OptimizationExecutionError: If the object type is unsupported,
            with code ``OPT_JSON_SERIALIZATION_FAILED``.
    """
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            warnings.warn(
                "NaN or Infinity value serialized as null",
                RuntimeWarning,
                stacklevel=2,
            )
            return None
        return obj
    if isinstance(obj, int | str):
        return obj
    if isinstance(obj, Decimal):
        return str(obj.normalize())
    if isinstance(obj, datetime):
        # Enforce UTC ISO-8601 — naive datetimes are assumed UTC.
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=UTC)
        return obj.astimezone(UTC).isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): json_safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [json_safe_serialize(v) for v in obj]
    if isinstance(obj, set | frozenset):
        # Sort for determinism; fall back to str-keyed sort for mixed
        # heterogeneous element types.
        try:
            items = sorted(obj)
        except TypeError:
            items = sorted(obj, key=str)
        return [json_safe_serialize(v) for v in items]

    obj_type = type(obj)
    msg = f"Unsupported serialization type: {obj_type}"
    raise OptimizationExecutionError(msg, code=OPT_JSON_SERIALIZATION_FAILED)


# ---------------------------------------------------------------------------
# Parametric simulation
# ---------------------------------------------------------------------------
def parametric_simulation(
    win_rate: float,
    reward_risk_ratio: float,
    risk_per_trade: float,
    trade_count: int,
    simulation_count: int,
    initial_balance: float,
    seed: int | None = None,
) -> dict[str, Any]:
    """Simulate account equity paths using win rate and reward/risk ratios.

    Uses a seeded ``random.Random`` instance for full reproducibility;
    does not mutate the global random state.

    Args:
        win_rate: Probability of a winning trade (0-1).
        reward_risk_ratio: Reward-to-risk ratio per trade.
        risk_per_trade: Fraction of balance risked per trade (e.g. 0.01).
        trade_count: Number of consecutive trades per simulation path.
        simulation_count: Total Monte Carlo iteration count.
        initial_balance: Starting account balance.
        seed: Optional random seed for full reproducibility.

    Returns:
        dict[str, Any]: Dictionary with keys ``equity_paths``,
            ``drawdowns``, and ``final_equity``.
    """
    rng = _random_module.Random(seed)
    equity_paths: list[list[float]] = []
    drawdowns: list[list[float]] = []
    final_equity: list[float] = []

    for _ in range(simulation_count):
        balance = initial_balance
        path = [balance]
        peak = balance
        dd_path = [0.0]
        for _ in range(trade_count):
            if rng.random() < win_rate:
                balance *= 1.0 + risk_per_trade * reward_risk_ratio
            else:
                balance *= 1.0 - risk_per_trade
            path.append(balance)
            peak = max(peak, balance)
            dd = (peak - balance) / peak if peak > 0 else 0.0
            dd_path.append(dd)
        equity_paths.append(path)
        drawdowns.append(dd_path)
        final_equity.append(balance)

    return {
        "equity_paths": equity_paths,
        "drawdowns": drawdowns,
        "final_equity": final_equity,
    }


# ---------------------------------------------------------------------------
# Tool context / envelope helpers
# ---------------------------------------------------------------------------
def optimization_tool_context(**kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
    """Extract standard request parameters from tool keyword arguments.

    Args:
        **kwargs: Keyword arguments from the calling tool, which may
            include ``request_id``, ``agent_name``, ``environment``,
            and ``dry_run``.

    Returns:
        dict[str, Any]: Normalized context dictionary.
    """
    return {
        "request_id": kwargs.get("request_id"),
        "agent_name": (kwargs.get("agent_name") or "optimization-agent"),
        "environment": (kwargs.get("environment") or "BACKTEST"),
        "dry_run": kwargs.get("dry_run", True),
    }


def optimization_business_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Strip routing headers and return only business logic fields.

    Args:
        payload: Full tool payload dictionary.

    Returns:
        dict[str, Any]: Payload with standard context fields removed.
    """
    business = dict(payload)
    for k in (
        "request_id",
        "agent_name",
        "environment",
        "dry_run",
        "correlation_id",
        "workflow_id",
    ):
        business.pop(k, None)
    return business


def package_optimization_request(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Validate and package a request envelope without executing jobs.

    Args:
        payload: Raw optimization request fields.

    Returns:
        dict[str, Any]: Validated, packaged request envelope.
    """
    from app.services.optimization.models import (
        OptimizationRequest,
    )

    dry_run = payload.get("dry_run", True)
    req = OptimizationRequest(**payload)
    req_hash = hashlib.sha256(
        canonical_json(req.model_dump()).encode("utf-8")
    ).hexdigest()[:12]

    return {
        "status": "success",
        "message": ("Optimization request packaged and validated successfully."),
        "data": {
            "run_id": f"packaged_{req_hash}",
            "dry_run": dry_run,
            "request_payload": req.model_dump(),
        },
    }


def optimization_tool_result(
    tool_name: str,
    status: str,
    request_id: str | None,
    data: Any,  # noqa: ANN401
    errors: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    audit: dict[str, Any] | None = None,
    side_effects: dict[str, Any] | None = None,
    start_time: float | None = None,
) -> StandardResponse:
    """Build the standard HaruQuant optimization result envelope.

    Args:
        tool_name: Name of the calling tool.
        status: Execution status string (``"success"``, ``"failed"``,
            ``"rejected"``).
        request_id: Optional correlation request ID.
        data: Payload data (must be JSON-safe or ``None``).
        errors: Optional list of structured error dictionaries.
        warnings: Optional list of warning strings.
        audit: Optional audit context dictionary.
        side_effects: Optional side-effect metadata dictionary.
        start_time: ``time.perf_counter()`` value captured at call start.

    Returns:
        StandardResponse: Normalized response envelope.
    """
    from app.utils.standard import (
        build_metadata,
        error_response,
        success_response,
    )

    inner = {
        "tool_name": tool_name,
        "status": status,
        "request_id": request_id,
        "data": data,
        "errors": errors or [],
        "warnings": warnings or [],
        "audit": audit or {},
        "side_effects": side_effects or {"places_trade": False},
    }

    metadata = build_metadata(
        tool_name=tool_name,
        start_time=start_time,
        request_id=request_id,
        reads=True,
    )

    if status in {"failed", "rejected"}:
        details = (
            str(errors[0].get("details") or "Execution failed")
            if errors
            else "Execution failed"
        )
        return error_response(
            message=f"Tool {tool_name} completed with status: {status}",
            code="TOOL_EXECUTION_FAILED",
            details=details,
            metadata=metadata,
        )

    return success_response(
        message=f"Tool {tool_name} completed successfully.",
        data=inner,
        metadata=metadata,
    )
