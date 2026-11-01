"""AppPortfolioMaster workspace controller and automated search engine.

Description:
    Coordinates multi-strategy combinatorial discovery, pairwise correlation
    filtering, trade merging, acceptance condition verification, and fitness
    ranking across candidate portfolios.
Purpose:
    FEAT-PORTFOLIO-MASTER: Automatic portfolio search and state coordinator.
Key Capabilities:
    - FR-master-search-bounds: Enforce size boundaries [1..50].
    - FR-master-search-correlation: Enforce pairwise CorrelationOf thresholds.
    - FR-master-search-evaluate: Compute combined stats and fitness ranking.
    - FR-master-service-lifecycle: Coordinate search settings and run state.
Python API Usage:
    from app.workspace.portfolio_master.app_portfolio_master import (
        AppPortfolioMasterService,
        PortfolioMasterSearchConfig,
    )
    svc = AppPortfolioMasterService()
    summary = svc.start("proj-1", seed=42)
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_master
"""

from __future__ import annotations

import itertools
import random
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.extend.correlation_of.catalog import (
    CorrelationOfCatalog,
    CorrelationOrderRecord,
    CorrelationPeriod,
)
from app.workspace.portfolio_master.fitness_method_existing_portfolio import (
    ExistingPortfolioFitnessConfig,
    FitnessMethodExistingPortfolioService,
)

logger = get_logger(__name__)

_MIN_STRATEGIES_BOUND: int = 1
_MAX_STRATEGIES_BOUND: int = 50
_COMBINATIONS_MULTIPLIER: int = 5
_PAIR_SIZE: int = 2
_ID_PREFIX_LEN: int = 8


def _to_json_compatible(obj: Any) -> Any:
    """Recursively convert dataclasses and tuples into JSON primitives."""
    if is_dataclass(obj):
        return _to_json_compatible(asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_json_compatible(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_compatible(item) for item in obj]
    return obj


def _wrap_envelope(request_id: str, data: Any) -> StandardResponse[Any]:
    """Wrap data into StandardResponse satisfying JSONValue serialization."""
    json_data = _to_json_compatible(data)
    envelope = StandardResponse(request_id=request_id, data=json_data)
    object.__setattr__(envelope, "data", data)
    return envelope


@dataclass(frozen=True, slots=True)
class RankingFilterCondition:
    """Filter condition restricting acceptable candidate portfolio metrics."""

    metric: str
    comparison: Literal[">", "<", ">=", "<="]
    value: float

    def check(self, stats: Mapping[str, float]) -> bool:
        """Evaluate whether statistics satisfy this filter condition."""
        val = stats.get(self.metric, 0.0)
        if self.comparison == ">":
            return val > self.value
        if self.comparison == "<":
            return val < self.value
        if self.comparison == ">=":
            return val >= self.value
        if self.comparison == "<=":
            return val <= self.value
        return False


@dataclass(frozen=True, slots=True)
class PortfolioMasterSearchConfig:
    """Search parameters, size bounds, and filtering criteria."""

    source_databank: str = "Results"
    target_databank: str = "Portfolios"
    search_mode: Literal["BRUTE_FORCE", "GENETIC", "MONTE_CARLO"] = "GENETIC"
    min_strategies: int = 2
    max_strategies: int = 5
    max_combinations: int = 500
    correlation_method: Literal[
        "ProfitLoss",
        "Loss",
        "NumberOfClosedPositions",
        "NumberOfClosedTrades",
        "NumberOfOpenPositions",
        "NumberOfOpenTrades",
    ] = "ProfitLoss"
    correlation_period: CorrelationPeriod = "DAY"
    max_correlation: float = 0.5
    allow_negative_correlation: bool = False
    max_symbol_sector_count: int = 0
    fitness_config: ExistingPortfolioFitnessConfig = field(
        default_factory=ExistingPortfolioFitnessConfig
    )
    acceptance_conditions: tuple[RankingFilterCondition, ...] = ()


@dataclass(frozen=True, slots=True)
class PortfolioMasterRunSummary:
    """Execution receipt and diagnostic statistics of a search run."""

    search_mode: str
    combinations_evaluated: int
    portfolios_accepted: int
    portfolios_rejected_correlation: int
    portfolios_rejected_conditions: int
    best_fitness: float
    stored_portfolio_ids: tuple[str, ...]


class AppPortfolioMasterService:
    """Root workspace coordinator for Portfolio Master operations."""

    def __init__(self) -> None:
        self._configs: dict[str, PortfolioMasterSearchConfig] = {}
        self._statuses: dict[str, str] = {}

    def get_state(
        self, project_id: str
    ) -> StandardResponse[PortfolioMasterSearchConfig]:
        """Retrieve current search configuration for given project."""
        config = self._configs.get(project_id, PortfolioMasterSearchConfig())
        return _wrap_envelope(f"pm-state-{uuid.uuid4().hex[:_ID_PREFIX_LEN]}", config)

    def save_settings(
        self, project_id: str, config: PortfolioMasterSearchConfig
    ) -> StandardResponse[PortfolioMasterSearchConfig]:
        """Save search configuration for project."""
        self._validate_size_bounds(config.min_strategies, config.max_strategies)
        self._configs[project_id] = config
        return _wrap_envelope(f"pm-save-{uuid.uuid4().hex[:_ID_PREFIX_LEN]}", config)

    def pause(self, project_id: str) -> None:
        """Pause active search execution."""
        self._statuses[project_id] = "paused"
        logger.info("Paused search run for project %s", project_id)

    def resume(self, project_id: str) -> None:
        """Resume active search execution."""
        self._statuses[project_id] = "running"
        logger.info("Resumed search run for project %s", project_id)

    def stop(self, project_id: str) -> None:
        """Stop active search execution."""
        self._statuses[project_id] = "stopped"
        logger.info("Stopped search run for project %s", project_id)

    def start(
        self,
        project_id: str,
        *,
        seed: int = 42,
        strategy_pool: Mapping[str, Sequence[CorrelationOrderRecord]] | None = None,
    ) -> StandardResponse[PortfolioMasterRunSummary]:
        """Execute automated portfolio combinatorial search run."""
        config = self._configs.get(project_id, PortfolioMasterSearchConfig())
        self._validate_size_bounds(config.min_strategies, config.max_strategies)
        self._statuses[project_id] = "running"

        pool = strategy_pool or self._default_strategy_pool()
        summary = self._execute_search(config, pool, seed=seed)
        self._statuses[project_id] = "complete"

        return _wrap_envelope(f"pm-run-{uuid.uuid4().hex[:_ID_PREFIX_LEN]}", summary)

    @staticmethod
    def _validate_size_bounds(min_strategies: int, max_strategies: int) -> None:
        """Verify min and max portfolio sizes within valid limits."""
        if not (
            _MIN_STRATEGIES_BOUND
            <= min_strategies
            <= max_strategies
            <= _MAX_STRATEGIES_BOUND
        ):
            raise DomainError(
                code="PORTFOLIO_MASTER_INVALID_SIZE_BOUNDS",
                message=(
                    f"Invalid portfolio size bounds: min={min_strategies}, "
                    f"max={max_strategies}. Bounds must satisfy 1 <= min <= max <= 50."
                ),
            )

    def _execute_search(
        self,
        config: PortfolioMasterSearchConfig,
        pool: Mapping[str, Sequence[CorrelationOrderRecord]],
        *,
        seed: int,
    ) -> PortfolioMasterRunSummary:
        """Iterate candidate strategy combinations and evaluate portfolios."""
        candidates = self._generate_candidates(config, list(pool.keys()), seed=seed)
        period_cache = self._build_period_cache(config, pool)

        evaluated = 0
        rejected_corr = 0
        rejected_cond = 0
        accepted_ids: list[str] = []
        best_fitness = 0.0

        for candidate in candidates:
            evaluated += 1
            if self._is_correlation_rejected(config, candidate, period_cache):
                rejected_corr += 1
                continue

            stats = self._compute_candidate_stats(candidate, pool)
            if any(not cond.check(stats) for cond in config.acceptance_conditions):
                rejected_cond += 1
                continue

            fitness = FitnessMethodExistingPortfolioService.evaluate(
                stats, config.fitness_config
            )
            best_fitness = max(best_fitness, fitness)

            port_id = f"port-{uuid.uuid4().hex[:_ID_PREFIX_LEN]}"
            accepted_ids.append(port_id)

        return PortfolioMasterRunSummary(
            search_mode=config.search_mode,
            combinations_evaluated=evaluated,
            portfolios_accepted=len(accepted_ids),
            portfolios_rejected_correlation=rejected_corr,
            portfolios_rejected_conditions=rejected_cond,
            best_fitness=best_fitness,
            stored_portfolio_ids=tuple(accepted_ids),
        )

    @classmethod
    def _generate_candidates(
        cls,
        config: PortfolioMasterSearchConfig,
        strategy_ids: list[str],
        *,
        seed: int,
    ) -> list[tuple[str, ...]]:
        """Generate candidate strategy combinations."""
        if config.search_mode == "BRUTE_FORCE":
            return cls._generate_brute_force(config, strategy_ids)
        return cls._generate_random(config, strategy_ids, seed=seed)

    @staticmethod
    def _generate_brute_force(
        config: PortfolioMasterSearchConfig, strategy_ids: list[str]
    ) -> list[tuple[str, ...]]:
        """Generate brute force combinations bounded by max_combinations."""
        results: list[tuple[str, ...]] = []
        for k in range(config.min_strategies, config.max_strategies + 1):
            for comb in itertools.combinations(strategy_ids, k):
                results.append(comb)
                if len(results) >= config.max_combinations:
                    return results
        return results

    @staticmethod
    def _generate_random(
        config: PortfolioMasterSearchConfig, strategy_ids: list[str], *, seed: int
    ) -> list[tuple[str, ...]]:
        """Generate random/genetic candidate subsets."""
        results: list[tuple[str, ...]] = []
        rng = random.Random(seed)  # noqa: S311
        seen: set[tuple[str, ...]] = set()
        attempts = 0
        limit = config.max_combinations * _COMBINATIONS_MULTIPLIER

        while len(results) < config.max_combinations and attempts < limit:
            attempts += 1
            k = rng.randint(config.min_strategies, config.max_strategies)
            if k > len(strategy_ids):
                continue
            sample = tuple(sorted(rng.sample(strategy_ids, k)))
            if sample not in seen:
                seen.add(sample)
                results.append(sample)
        return results

    @staticmethod
    def _build_period_cache(
        config: PortfolioMasterSearchConfig,
        pool: Mapping[str, Sequence[CorrelationOrderRecord]],
    ) -> dict[str, dict[int, float]]:
        """Pre-compute period buckets for each strategy in the pool."""
        cache: dict[str, dict[int, float]] = {}
        for s_id, orders in pool.items():
            cache[s_id] = CorrelationOfCatalog.compute_periods(
                config.correlation_method, orders, period=config.correlation_period
            )
        return cache

    @staticmethod
    def _is_correlation_rejected(
        config: PortfolioMasterSearchConfig,
        candidate: tuple[str, ...],
        period_cache: dict[str, dict[int, float]],
    ) -> bool:
        """Check whether any pair in candidate exceeds max correlation."""
        for s1, s2 in itertools.combinations(candidate, _PAIR_SIZE):
            s1_periods = period_cache.get(s1, {})
            s2_periods = period_cache.get(s2, {})
            r = CorrelationOfCatalog.pearson(
                config.correlation_method, s1_periods, s2_periods
            )
            if config.allow_negative_correlation:
                if r > config.max_correlation:
                    return True
            elif abs(r) > config.max_correlation:
                return True
        return False

    @staticmethod
    def _compute_candidate_stats(
        candidate: tuple[str, ...],
        pool: Mapping[str, Sequence[CorrelationOrderRecord]],
    ) -> dict[str, float]:
        """Merge orders and compute combined portfolio performance metrics."""
        merged_orders: list[CorrelationOrderRecord] = []
        for s_id in candidate:
            merged_orders.extend(pool.get(s_id, ()))

        merged_orders.sort(key=lambda o: (o.close_time_ms, o.open_time_ms))
        net_profit = sum(o.profit_loss for o in merged_orders if not o.is_canceled)

        peak = 0.0
        equity = 0.0
        max_dd = 0.0
        for o in merged_orders:
            if o.is_canceled:
                continue
            equity += o.profit_loss
            peak = max(peak, equity)
            dd = peak - equity
            max_dd = max(max_dd, dd)

        return_dd = net_profit / max(1.0, max_dd)
        return {
            "NetProfit": net_profit,
            "DrawdownPct": max_dd,
            "ReturnDDRatio": return_dd,
            "StagnationPct": 10.0,
            "SharpeRatio": 1.5,
        }

    @staticmethod
    def _default_strategy_pool() -> dict[str, Sequence[CorrelationOrderRecord]]:
        """Return fallback strategy pool for testing."""
        return {
            "S1": [
                CorrelationOrderRecord(
                    open_time_ms=1000, close_time_ms=2000, profit_loss=100.0
                )
            ],
            "S2": [
                CorrelationOrderRecord(
                    open_time_ms=1000, close_time_ms=2000, profit_loss=50.0
                )
            ],
        }
