"""Optimization genetic search algorithm.

Provides parameter optimization through population reproduction, crossover,
mutation, elitism, and fitness scoring.
"""

from __future__ import annotations

import random
import time
from typing import Any

from pydantic import BaseModel, Field

from app.services.optimization.algorithms.grid import check_constraints
from app.services.optimization.algorithms.random import sample_parameter
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


class GeneticAlgorithmResult(BaseModel):
    """Result of a genetic algorithm optimization run.

    Attributes:
        best_parameters: Highest-scoring parameter candidate.
        best_score: Highest objective score achieved.
        objective: Optimization target metric.
        generations: Generation steps run.
        population_size: Individuals count in each generation.
        runtime_ms: Total duration in milliseconds.
    """

    best_parameters: dict[str, Any] = Field(..., description="Best parameters.")
    best_score: float = Field(..., description="Top score achieved.")
    objective: str = Field(..., description="Objective metric name.")
    generations: int = Field(..., description="Generations count.")
    population_size: int = Field(..., description="Population size.")
    runtime_ms: float = Field(..., description="Duration in milliseconds.")


def crossover(
    parent_a: dict[str, Any],
    parent_b: dict[str, Any],
    space: ParameterSpace,
    rng: random.Random,
) -> dict[str, Any]:
    """Combine parameters of two parents to produce an offspring.

    Args:
        parent_a: First parent parameters dictionary.
        parent_b: Second parent parameters dictionary.
        space: Parameter space schema defining bounds.
        rng: Seeded ``random.Random`` instance.

    Returns:
        dict[str, Any]: Offspring parameter dictionary.
    """
    offspring: dict[str, Any] = {}
    for p in space.parameters:
        val_a = parent_a.get(p.name)
        val_b = parent_b.get(p.name)
        if val_a is None:
            offspring[p.name] = val_b
        elif val_b is None:
            offspring[p.name] = val_a
        elif p.type in ("categorical", "bool", "fixed") or rng.random() < 0.5:  # noqa: PLR2004
            offspring[p.name] = rng.choice([val_a, val_b])
        else:
            avg = (float(val_a) + float(val_b)) / 2.0
            if p.type == "int":
                offspring[p.name] = round(avg)
            else:
                offspring[p.name] = round(avg, 8)
    return offspring


def mutate(
    params: dict[str, Any],
    space: ParameterSpace,
    mutation_rate: float,
    rng: random.Random,
) -> dict[str, Any]:
    """Randomly mutate parameter values in a candidate dictionary.

    Fixed parameters are never mutated regardless of ``mutation_rate``.

    Args:
        params: Parameters to mutate.
        space: Parameter space schema defining bounds.
        mutation_rate: Mutation probability per parameter (0-1).
        rng: Seeded ``random.Random`` instance.

    Returns:
        dict[str, Any]: Mutated parameters.
    """
    mutated = dict(params)
    for p in space.parameters:
        if p.type == "fixed":
            continue
        if rng.random() < mutation_rate:
            mutated[p.name] = sample_parameter(p, rng)
    return mutated


def genetic_algorithm(  # noqa: C901, PLR0912, PLR0915
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    population_size: int = 20,
    generations: int = 5,
    mutation_rate: float = 0.1,
    elitism_rate: float = 0.1,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> OptimizationSummary:
    """Evolve parameter candidates using a genetic algorithm.

    Args:
        strategy_ref: Target strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        population_size: Individuals per generation.
        generations: Number of evolutionary steps to run.
        mutation_rate: Per-parameter mutation probability (0-1).
        elitism_rate: Top fraction of population preserved each generation.
        seed: Random seed for deterministic reproducibility.
        **kwargs: Additional adapter options (e.g. ``dry_run``).

    Returns:
        OptimizationSummary: Evaluated candidates summary.
    """
    dry_run = kwargs.get("dry_run", True)
    start_time = time.perf_counter()
    rng = random.Random(seed)

    population: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    attempts = 0
    max_attempts = population_size * 20

    while len(population) < population_size and attempts < max_attempts:
        attempts += 1
        ind = {p.name: sample_parameter(p, rng) for p in parameter_space.parameters}
        try:
            if not check_constraints(ind, parameter_space.constraints):
                continue
        except ValidationError:
            raise
        except Exception:  # noqa: BLE001,S112
            continue
        h = build_candidate_hash(
            strategy_hash=strategy_ref,
            data_hash=f"{start}_{end}",
            cost_model_hash="default",
            realism_profile_hash="default",
            objective_hash=objective,
            engine_type="event_driven",
            module_version="1.0.0",
            parameters=ind,
            space=parameter_space,
        )
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        population.append(ind)

    evaluated_cache: dict[str, OptimizationResult] = {}
    total_evals = 0

    def evaluate_individual(ind: dict[str, Any]) -> OptimizationResult | None:
        nonlocal total_evals
        cand_hash = build_candidate_hash(
            strategy_hash=strategy_ref,
            data_hash=f"{start}_{end}",
            cost_model_hash="default",
            realism_profile_hash="default",
            objective_hash=objective,
            engine_type="event_driven",
            module_version="1.0.0",
            parameters=ind,
            space=parameter_space,
        )
        if cand_hash in evaluated_cache:
            return evaluated_cache[cand_hash]

        total_evals += 1
        if dry_run:
            res = evaluate_candidate_score(
                [], initial_balance, objective, trial_count=total_evals
            )
            result_item = OptimizationResult(
                parameters=ind,
                score=res["score"],
                metrics=res,
                metadata={"candidate_hash": cand_hash, "dry_run": True},
            )
        else:
            try:
                bt_res = run_strategy_backtest(
                    strategy_ref=strategy_ref,
                    symbols=symbols,
                    timeframe=timeframe,
                    start=start,
                    end=end,
                    parameters=ind,
                    initial_balance=initial_balance,
                    **kwargs,
                )
                res = evaluate_candidate_score(
                    bt_res.trades,
                    initial_balance,
                    objective,
                    trial_count=total_evals,
                )
                result_item = OptimizationResult(
                    parameters=ind,
                    score=res["score"],
                    metrics=res,
                    metadata={"candidate_hash": cand_hash},
                )
            except OptimizationExecutionError as exc:
                logger.error("Candidate execution failed in GA: %s", exc)
                return None

        evaluated_cache[cand_hash] = result_item
        return result_item

    def tournament_selection(
        fit_res: list[tuple[dict[str, Any], OptimizationResult]],
        k: int = 3,
    ) -> dict[str, Any]:
        chosen = rng.sample(fit_res, k=min(k, len(fit_res)))
        chosen.sort(key=lambda x: x[1].score, reverse=True)
        return chosen[0][0]

    for gen in range(generations):
        fitness_results: list[tuple[dict[str, Any], OptimizationResult]] = []
        for ind in population:
            res = evaluate_individual(ind)
            if res is not None:
                fitness_results.append((ind, res))

        if not fitness_results:
            break

        fitness_results.sort(key=lambda x: x[1].score, reverse=True)

        if gen == generations - 1:
            break

        num_elites = max(1, int(population_size * elitism_rate))
        next_population: list[dict[str, Any]] = [
            item[0] for item in fitness_results[:num_elites]
        ]

        while len(next_population) < population_size:
            parent_a = tournament_selection(fitness_results)
            parent_b = tournament_selection(fitness_results)
            child = crossover(parent_a, parent_b, parameter_space, rng)
            child = mutate(child, parameter_space, mutation_rate, rng)

            try:
                if not check_constraints(child, parameter_space.constraints):
                    continue
            except ValidationError:
                raise
            except Exception:  # noqa: BLE001,S112
                continue

            next_population.append(child)

        population = next_population

    all_results = list(evaluated_cache.values())
    best_cand, best_score = select_best_candidate(all_results)
    runtime_ms = (time.perf_counter() - start_time) * 1000
    return OptimizationSummary(
        best_candidate=best_cand,
        best_score=best_score,
        objective=objective,
        runtime_ms=runtime_ms,
        total_candidates=len(all_results),
        candidates=all_results,
    )


def optimization_genetic(
    strategy_ref: str,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    parameter_space: ParameterSpace,
    objective: str = "sharpe",
    initial_balance: float = 10000.0,
    population_size: int = 20,
    generations: int = 5,
    seed: int | None = None,
    **kwargs: Any,  # noqa: ANN401
) -> dict[str, Any]:
    """User-facing wrapper for genetic algorithm parameter optimization.

    Constructs a typed :class:`GeneticAlgorithmResult` from the underlying
    summary before returning the normalized response dictionary.

    Args:
        strategy_ref: Target strategy registration reference.
        symbols: Symbol ticker list.
        timeframe: Bar resolution timeframe string.
        start: ISO start date.
        end: ISO end date.
        parameter_space: Parameter space boundaries.
        objective: Target optimization metric name.
        initial_balance: Starting account balance.
        population_size: Individuals per generation.
        generations: Number of evolutionary steps.
        seed: Random seed for deterministic reproducibility.
        **kwargs: Additional adapter options.

    Returns:
        dict[str, Any]: Standard response dictionary with keys
            ``"status"``, ``"message"``, and ``"data"``.
    """
    try:
        start_time = time.perf_counter()
        summary = genetic_algorithm(
            strategy_ref=strategy_ref,
            symbols=symbols,
            timeframe=timeframe,
            start=start,
            end=end,
            parameter_space=parameter_space,
            objective=objective,
            initial_balance=initial_balance,
            population_size=population_size,
            generations=generations,
            seed=seed,
            **kwargs,
        )
        runtime_ms = (time.perf_counter() - start_time) * 1000

        typed_result = GeneticAlgorithmResult(
            best_parameters=summary.best_candidate.parameters,
            best_score=summary.best_score,
            objective=objective,
            generations=generations,
            population_size=population_size,
            runtime_ms=runtime_ms,
        )
        return {
            "status": "success",
            "message": "Genetic parameter optimization completed.",
            "data": typed_result.model_dump(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "message": f"Genetic optimization failed: {exc}",
            "error": {
                "code": getattr(exc, "code", "OPT_EXECUTION_FAILED"),
                "details": str(exc),
            },
        }
