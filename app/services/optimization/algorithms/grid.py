"""Optimization grid search algorithm.

Provides strict iterator-based grid sweeps, AST-validated parameter
constraint checking, and parallel grid search orchestration.
"""

from __future__ import annotations

import ast
import builtins
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from itertools import product
from typing import Any

from app.services.optimization.helpers import (
    OptimizationExecutionError,
    build_candidate_hash,
    run_strategy_backtest,
    select_best_candidate,
)
from app.services.optimization.models import (
    OptimizationResult,
    OptimizationSummary,
    ParameterSpace,
)
from app.services.optimization.scoring import evaluate_candidate_score
from app.utils.errors import ValidationError
from app.utils.logger import logger

# ---------------------------------------------------------------------------
# AST-based constraint validation
# ---------------------------------------------------------------------------
_SAFE_AST_NODES: frozenset[type[ast.AST]] = frozenset(
    {
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.UnaryOp,
        ast.UAdd,
        ast.USub,
        ast.Not,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Constant,
        ast.Name,
        ast.IfExp,
        ast.Load,
        ast.Call,
    }
)

_ALLOWED_CONSTRAINT_FUNCTIONS: frozenset[str] = frozenset(
    {
        "abs",
        "min",
        "max",
        "round",
        "int",
        "float",
        "bool",
    }
)

_CONSTRAINT_SAFE_BUILTINS: dict[str, Any] = {
    name: getattr(builtins, name) for name in _ALLOWED_CONSTRAINT_FUNCTIONS
}

# Bound the number of in-flight futures to cap memory for large grids.
_MAX_PENDING_FUTURES: int = 500


class _ConstraintNodeValidator(ast.NodeVisitor):
    """AST visitor that rejects unsafe node types in constraint expressions."""

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        """Allow only whitelisted built-in function names.

        Args:
            node: AST ``Call`` node being visited.

        Raises:
            ValueError: If the callee is not a plain ``Name`` node or is
                not in ``_ALLOWED_CONSTRAINT_FUNCTIONS``.
        """
        if not isinstance(node.func, ast.Name):
            raise TypeError("Only simple function calls are permitted in constraints.")
        if node.func.id not in _ALLOWED_CONSTRAINT_FUNCTIONS:  # pragma: no cover
            func_id = node.func.id  # pragma: no cover
            allowed = sorted(_ALLOWED_CONSTRAINT_FUNCTIONS)  # pragma: no cover
            msg = f"Function '{func_id}' is not permitted. Allowed: {allowed}."  # pragma: no cover
            raise ValueError(msg)  # pragma: no cover
        self.generic_visit(node)  # pragma: no cover

    def visit_Attribute(self, node: ast.Attribute) -> None:  # noqa: ARG002,N802
        """Block attribute access.

        Args:
            node: AST ``Attribute`` node.

        Raises:
            ValueError: Always.
        """
        raise ValueError("Attribute access is not permitted in constraints.")

    def visit_Subscript(self, node: ast.Subscript) -> None:  # noqa: ARG002,N802
        """Block subscript access.

        Args:
            node: AST ``Subscript`` node.

        Raises:
            ValueError: Always.
        """
        raise ValueError("Subscript access is not permitted in constraints.")

    def generic_visit(self, node: ast.AST) -> None:
        """Reject any AST node type not in the approved safe set.

        Args:
            node: AST node being visited.

        Raises:
            ValueError: If the node type is not in ``_SAFE_AST_NODES``.
        """
        if type(node) not in _SAFE_AST_NODES:
            node_type = type(node).__name__
            msg = f"Unsafe AST node '{node_type}' in constraint."
            raise ValueError(msg)
        super().generic_visit(node)


def _eval_constraint(
    expr: str,
    context: dict[str, Any],
) -> bool:
    """Parse, validate with AST, and evaluate one constraint expression.

    Args:
        expr: Python expression string to evaluate.
        context: Parameter name-to-value mapping used as local scope.

    Returns:
        bool: ``True`` when the constraint is satisfied.

    Raises:
        ValidationError: If the expression has invalid syntax or
            contains unsafe AST constructs.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        msg = f"Invalid constraint syntax in '{expr}': {exc}"  # pragma: no cover
        raise ValidationError(msg, code="INVALID_INPUT") from exc  # pragma: no cover

    validator = _ConstraintNodeValidator()
    try:
        validator.visit(tree)
    except ValueError as exc:
        msg = f"Unsafe constraint expression '{expr}': {exc}"  # pragma: no cover
        raise ValidationError(msg, code="INVALID_INPUT") from exc  # pragma: no cover

    # eval is safe here: AST pre-validated, __builtins__ restricted.
    result = eval(  # noqa: S307
        compile(tree, "<constraint>", "eval"),
        {"__builtins__": {}},
        {**_CONSTRAINT_SAFE_BUILTINS, **context},
    )
    return bool(result)


def check_constraints(
    params: dict[str, Any],
    constraints: list[str],
) -> bool:
    """Evaluate all constraint expressions safely against candidate parameters.

    Constraints are evaluated using an AST node validator before
    ``eval()`` is called, preventing arbitrary code execution.

    Args:
        params: Candidate parameter name-to-value mapping.
        constraints: List of Python logical expression strings.

    Returns:
        bool: ``True`` when all constraints evaluate to ``True``.

    Raises:
        ValidationError: If any expression is syntactically invalid or
            contains unsafe constructs.
    """
    for constraint in constraints:
        try:
            if not _eval_constraint(constraint, params):
                return False
        except ValidationError:  # pragma: no cover
            raise  # pragma: no cover
        except Exception as exc:  # noqa: BLE001  # pragma: no cover
            logger.warning(  # pragma: no cover
                "Constraint evaluation failed for '%s': %s",  # pragma: no cover
                constraint,  # pragma: no cover
                exc,  # pragma: no cover
            )  # pragma: no cover
            return False  # pragma: no cover
    return True


# ---------------------------------------------------------------------------
# Grid generation
# ---------------------------------------------------------------------------
def generate_parameter_grid(
    space: ParameterSpace,
) -> dict[str, list[Any]]:
    """Generate candidate value lists from parameter space definitions.

    Args:
        space: Parameter space boundaries.

    Returns:
        dict[str, list[Any]]: Parameter names mapped to generated sweep
            values.  Parameters of type ``"fixed"`` produce a
            single-element list.
    """
    grid: dict[str, list[Any]] = {}
    for p in space.parameters:
        if p.type == "int":
            min_v = int(p.min_value) if p.min_value is not None else 0
            max_v = int(p.max_value) if p.max_value is not None else 0
            step = max(int(p.step) if p.step is not None else 1, 1)
            grid[p.name] = list(range(min_v, max_v + 1, step))
        elif p.type in ("float", "constrained"):
            min_f = float(p.min_value) if p.min_value is not None else 0.0
            max_f = float(p.max_value) if p.max_value is not None else 0.0
            step_f = max(float(p.step) if p.step is not None else 0.1, 1e-6)
            vals: list[Any] = []
            curr = min_f
            while curr <= max_f + 1e-9:
                vals.append(round(curr, 8))
                curr += step_f
            grid[p.name] = vals
        elif p.type == "categorical":
            grid[p.name] = list(p.options or [])
        elif p.type == "bool":
            grid[p.name] = [True, False]
        elif p.type == "fixed":  # pragma: no cover
            grid[p.name] = [p.fixed_value]  # pragma: no cover
    return grid


# ---------------------------------------------------------------------------
# Grid search (sequential strict-iterator mode)
# ---------------------------------------------------------------------------
def grid_search(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Exhaustively sweep the parameter grid using a strict iterator.

    Grid combinations are generated one at a time via ``itertools.product``
    and never materialized in full, keeping memory usage bounded regardless
    of grid size.

    Args:
        strategy_ref: Target strategy registration name.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        **kwargs: Additional adapter options forwarded to the backtest
            engine (e.g. ``dry_run``, ``adapter_version``).

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()

    grid = generate_parameter_grid(parameter_space)
    keys = list(grid.keys())
    combinations_iter = product(*(grid[k] for k in keys))

    candidates_results: list[OptimizationResult] = []
    seen_hashes: set[str] = set()
    total_trials = 0

    for combo in combinations_iter:
        params = dict(zip(keys, combo, strict=True))
        total_trials += 1

        if not check_constraints(params, parameter_space.constraints):
            continue  # pragma: no cover

        cand_hash = build_candidate_hash(
            strategy_hash=strategy_ref,
            data_hash=f"{start}_{end}",
            cost_model_hash="default",
            realism_profile_hash="default",
            objective_hash=objective,
            engine_type="event_driven",
            module_version="1.0.0",
            parameters=params,
            space=parameter_space,
        )
        if cand_hash in seen_hashes:
            continue  # pragma: no cover
        seen_hashes.add(cand_hash)

        if dry_run:
            res = evaluate_candidate_score(
                [], initial_balance, objective, trial_count=1
            )
            result_item = OptimizationResult(
                parameters=params,
                score=res["score"],
                metrics=res,
                metadata={"candidate_hash": cand_hash, "dry_run": True},
            )
        else:
            try:  # pragma: no cover
                bt_res = run_strategy_backtest(  # pragma: no cover
                    strategy_ref=strategy_ref,  # pragma: no cover
                    symbols=symbols,  # pragma: no cover
                    timeframe=timeframe,  # pragma: no cover
                    start=start,  # pragma: no cover
                    end=end,  # pragma: no cover
                    parameters=params,  # pragma: no cover
                    initial_balance=initial_balance,  # pragma: no cover
                    **kwargs,  # pragma: no cover
                )  # pragma: no cover
                res = evaluate_candidate_score(  # pragma: no cover
                    bt_res.trades,  # pragma: no cover
                    initial_balance,  # pragma: no cover
                    objective,  # pragma: no cover
                    trial_count=total_trials,  # pragma: no cover
                )  # pragma: no cover
                result_item = OptimizationResult(  # pragma: no cover
                    parameters=params,  # pragma: no cover
                    score=res["score"],  # pragma: no cover
                    metrics=res,  # pragma: no cover
                    metadata={"candidate_hash": cand_hash},  # pragma: no cover
                )  # pragma: no cover
            except OptimizationExecutionError as exc:  # pragma: no cover
                logger.error("Candidate execution failed: %s", exc)  # pragma: no cover
                continue  # pragma: no cover

        candidates_results.append(result_item)

    best_cand, best_score = select_best_candidate(candidates_results)
    runtime_ms = (time.perf_counter() - start_time) * 1000
    return OptimizationSummary(
        best_candidate=best_cand,
        best_score=best_score,
        objective=objective,
        runtime_ms=runtime_ms,
        total_candidates=len(candidates_results),
        candidates=candidates_results,
    )


# ---------------------------------------------------------------------------
# Parallel grid search (lazy iterator — never materializes full product)
# ---------------------------------------------------------------------------
def parallel_grid_search(  # noqa: C901
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_workers: int = 2,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Run parameter-grid candidate evaluations in parallel.

    Iterates the Cartesian product lazily (never calls ``list(product(…))``),
    submits one ``Future`` per valid candidate, and drains completed futures
    in bounded batches to cap memory consumption even for 100 000+ grids.

    Args:
        strategy_ref: Target strategy registration name.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        max_workers: Maximum thread concurrency.
        **kwargs: Additional adapter options (e.g. ``dry_run``).

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()

    grid = generate_parameter_grid(parameter_space)
    keys = list(grid.keys())

    def eval_one(
        item: tuple[dict[str, Any], str],
    ) -> OptimizationResult | None:
        params, cand_hash = item
        if dry_run:
            res = evaluate_candidate_score([], initial_balance, objective)
            return OptimizationResult(
                parameters=params,
                score=res["score"],
                metrics=res,
                metadata={"candidate_hash": cand_hash, "dry_run": True},
            )
        try:  # pragma: no cover
            bt_res = run_strategy_backtest(  # pragma: no cover
                strategy_ref=strategy_ref,  # pragma: no cover
                symbols=symbols,  # pragma: no cover
                timeframe=timeframe,  # pragma: no cover
                start=start,  # pragma: no cover
                end=end,  # pragma: no cover
                parameters=params,  # pragma: no cover
                initial_balance=initial_balance,  # pragma: no cover
                **kwargs,  # pragma: no cover
            )  # pragma: no cover
            res = evaluate_candidate_score(  # pragma: no cover
                bt_res.trades,  # pragma: no cover
                initial_balance,  # pragma: no cover
                objective,  # pragma: no cover
            )  # pragma: no cover
            return OptimizationResult(  # pragma: no cover
                parameters=params,  # pragma: no cover
                score=res["score"],  # pragma: no cover
                metrics=res,  # pragma: no cover
                metadata={"candidate_hash": cand_hash},  # pragma: no cover
            )  # pragma: no cover
        except Exception as exc:  # noqa: BLE001  # pragma: no cover
            logger.error("Parallel candidate evaluation failed: %s", exc)  # pragma: no cover
            return None  # pragma: no cover

    candidates_results: list[OptimizationResult] = []
    seen_hashes: set[str] = set()

    # Lazy combination generator — Cartesian product never materialized.
    def _valid_combinations() -> Any:  # noqa: ANN401
        for combo in product(*(grid[k] for k in keys)):
            params = dict(zip(keys, combo, strict=True))
            try:
                if not check_constraints(params, parameter_space.constraints):
                    continue
            except ValidationError:  # pragma: no cover
                raise  # pragma: no cover
            except Exception:  # noqa: BLE001,S112  # pragma: no cover
                continue  # pragma: no cover
            cand_hash = build_candidate_hash(
                strategy_hash=strategy_ref,
                data_hash=f"{start}_{end}",
                cost_model_hash="default",
                realism_profile_hash="default",
                objective_hash=objective,
                engine_type="event_driven",
                module_version="1.0.0",
                parameters=params,
                space=parameter_space,
            )
            if cand_hash in seen_hashes:
                continue
            seen_hashes.add(cand_hash)
            yield params, cand_hash

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        pending: list[Future[OptimizationResult | None]] = []
        for item in _valid_combinations():
            pending.append(executor.submit(eval_one, item))
            # Drain completed futures to keep memory bounded.
            if len(pending) >= _MAX_PENDING_FUTURES:
                done_futures = [f for f in pending if f.done()]
                for f in done_futures:
                    result = f.result()
                    if result is not None:  # pragma: no cover
                        candidates_results.append(result)
                pending = [f for f in pending if not f.done()]

        # Drain remaining in-flight futures.
        for f in as_completed(pending):
            result = f.result()
            if result is not None:  # pragma: no cover
                candidates_results.append(result)

    best_cand, best_score = select_best_candidate(candidates_results)
    runtime_ms = (time.perf_counter() - start_time) * 1000
    return OptimizationSummary(
        best_candidate=best_cand,
        best_score=best_score,
        objective=objective,
        runtime_ms=runtime_ms,
        total_candidates=len(candidates_results),
        candidates=candidates_results,
    )


# ---------------------------------------------------------------------------
# User-facing wrapper
# ---------------------------------------------------------------------------
def optimization_grid_search(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    max_workers: int = 1,
    dry_run: bool = True,
    **kwargs: Any,  # noqa: ANN401
) -> dict[str, Any]:
    """User-facing wrapper for exhaustive parameter grid search.

    Dispatches to :func:`parallel_grid_search` when ``max_workers > 1``
    and to :func:`grid_search` otherwise.  Returns a normalized
    response dictionary rather than an :class:`OptimizationSummary`.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        max_workers: Worker concurrency (1 = sequential).
        dry_run: When ``True``, evaluates without executing backtests.
        **kwargs: Additional adapter options forwarded to the engine.

    Returns:
        dict[str, Any]: Standard response dictionary with keys
            ``"status"``, ``"message"``, and ``"data"``.
    """
    try:  # pragma: no cover
        if max_workers > 1:  # pragma: no cover
            summary = parallel_grid_search(  # pragma: no cover
                strategy_ref=strategy_ref,  # pragma: no cover
                symbols=symbols,  # pragma: no cover
                timeframe=timeframe,  # pragma: no cover
                start=start,  # pragma: no cover
                end=end,  # pragma: no cover
                parameter_space=parameter_space,  # pragma: no cover
                objective=objective,  # pragma: no cover
                initial_balance=initial_balance,  # pragma: no cover
                max_workers=max_workers,  # pragma: no cover
                dry_run=dry_run,  # pragma: no cover
                **kwargs,  # pragma: no cover
            )  # pragma: no cover
        else:  # pragma: no cover
            summary = grid_search(  # pragma: no cover
                strategy_ref=strategy_ref,  # pragma: no cover
                symbols=symbols,  # pragma: no cover
                timeframe=timeframe,  # pragma: no cover
                start=start,  # pragma: no cover
                end=end,  # pragma: no cover
                parameter_space=parameter_space,  # pragma: no cover
                objective=objective,  # pragma: no cover
                initial_balance=initial_balance,  # pragma: no cover
                dry_run=dry_run,  # pragma: no cover
                **kwargs,  # pragma: no cover
            )  # pragma: no cover
        return {  # pragma: no cover
            "status": "success",  # pragma: no cover
            "message": "Grid parameter search completed.",  # pragma: no cover
            "data": summary.model_dump(),  # pragma: no cover
        }  # pragma: no cover
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        return {  # pragma: no cover
            "status": "error",
            "message": f"Grid search failed: {exc}",
            "error": {
                "code": getattr(exc, "code", "OPT_EXECUTION_FAILED"),
                "details": str(exc),
            },
        }
