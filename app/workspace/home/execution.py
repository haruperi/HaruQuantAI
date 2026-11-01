"""Core-backed, snapshot-isolated Home task execution.

Description:
    Resolves native tasks and catalog bars before submission, then evaluates
    generated or stored strategies with the Core runtime/backtest engine. Results
    retain strategy definitions, execution provenance, trades, equity and excursions.
Purpose:
    FEAT-HOME-EXECUTION: Replace simulated research results with actual evaluation.
Key Capabilities:
    - FR-home-execution-preflight: Validate immutable project/data/strategy snapshots;
      acceptance tests verify rejection before submission and explicit logs.
    - FR-home-execution-evaluate: Evaluate bounded candidates cooperatively and store
      unique runs; numerical tests verify trades, progress and persistence logs.
    - FR-home-execution-finite: Reject non-finite metrics before persistence;
      acceptance tests verify that no replacement metrics are fabricated.
Python API Usage:
    snapshot = executor.prepare(project, task_id, revision)
    receipt = executor.run(context, snapshot)
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_execution_acceptance.py --no-cov
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any, cast

from pydantic import TypeAdapter, ValidationError

from app.core.data.catalog import DataCatalog, DatasetRef
from app.core.data.contracts import MarketBar
from app.core.enums import Timeframe
from app.core.host.logging import get_logger
from app.core.jobs.manager import JobContext
from app.core.lib.errors import DomainError, JSONValue
from app.core.trading.backtest.contracts import RunSpec
from app.core.trading.backtest.runner import BacktestRunner
from app.core.trading.generation.engine import GenerationEngine, GenerationSpec
from app.core.trading.optimization.engine import OptimizationEngine, ParameterRange
from app.core.trading.project.contracts import ProjectDocument
from app.core.trading.results.adapters import from_backtest_result
from app.core.trading.results.store import ResultStore
from app.core.trading.statistics.contracts import SampleSplit
from app.core.trading.statistics.service import StatisticsService
from app.core.trading.strategy.contracts import ActionKind, StrategyDocument
from app.core.trading.strategy.runtime import StrategyRuntime
from app.extend.blocks.money_management.sizers import FixedSize
from app.workspace.home.contracts import ExecutionSettings

logger = get_logger(__name__)
_STRATEGY = TypeAdapter(StrategyDocument)
_MAX_BARS = 100000
_TASK_MODES = {
    "build": "RANDOM",
    "builder": "RANDOM",
    "retest": "RETEST",
    "retester": "RETEST",
    "optimize": "GRID",
    "optimizer": "GRID",
}


@dataclass(frozen=True, slots=True)
class ExecutionSnapshot:
    """Detached execution inputs unaffected by subsequent project edits."""

    project_id: str
    task_id: str
    project_revision: int
    databank_id: str
    config_json: str
    bars: tuple[MarketBar, ...]
    strategies_json: tuple[str, ...]


class ProjectExecutor:
    """Orchestrate Core owners using injected catalog and result capabilities."""

    def __init__(self, catalog: DataCatalog, results: ResultStore) -> None:
        self.catalog = catalog
        self.results = results

    def prepare(
        self,
        project: ProjectDocument,
        task_id: str | None,
        revision: int | None,
    ) -> ExecutionSnapshot:
        """Validate authority and capture actual bars before submitting any work."""
        current = project.metadata.get("revision", 1)
        if isinstance(revision, bool) or revision is None or current != revision:
            raise DomainError(
                code="CONFLICT", message="A current project revision is required"
            )
        task = project.tasks.get(task_id or "")
        if task is None or not task.enabled or task.task_id != task_id:
            raise DomainError(
                code="TASK_NOT_FOUND", message="Select an enabled saved task"
            )
        mode = _TASK_MODES.get(task.task_type.lower())
        if mode is None:
            raise DomainError(
                code="UNSUPPORTED_TASK", message="Task type has no execution algorithm"
            )
        try:
            settings = ExecutionSettings.model_validate(task.settings.get("execution"))
            timeframe = Timeframe(settings.dataset.timeframe)
        except (ValidationError, ValueError, TypeError) as error:
            raise DomainError(
                code="INVALID_EXECUTION_SETTINGS",
                message="Saved execution settings are invalid or unsupported",
            ) from error
        if settings.mode != mode:
            raise DomainError(
                code="UNSUPPORTED_MODE",
                message="Execution mode does not match saved task type",
            )
        bank = task.databank_target
        if not bank or bank not in project.databanks.values():
            raise DomainError(
                code="DATABANK_NOT_FOUND",
                message="Task destination must belong to this project",
            )
        pinned, bars = self._read_bars(settings, timeframe)
        strategies = self._read_strategies(project, settings)
        config = settings.model_dump(mode="json")
        config["dataset"]["revision"] = pinned.revision
        logger.info(
            "FR-home-execution-preflight: captured task %s with %d bars",
            task_id,
            len(bars),
        )
        return ExecutionSnapshot(
            project.manifest.project_id,
            task.task_id,
            revision,
            bank,
            json.dumps(config, allow_nan=False),
            bars,
            tuple(strategies),
        )

    def _read_bars(
        self,
        settings: ExecutionSettings,
        timeframe: Timeframe,
    ) -> tuple[DatasetRef, tuple[MarketBar, ...]]:
        """Pin the catalog revision and detach bounded chronological bars."""
        reference = DatasetRef(
            symbol=settings.dataset.symbol,
            timeframe=timeframe,
            source=settings.dataset.source,
            revision=settings.dataset.revision,
        )
        info = self.catalog.get_dataset_info(reference)
        if info is None or not info.updated_at_utc:
            raise DomainError(
                code="DATASET_NOT_FOUND",
                message="A versioned catalog dataset is required",
            )
        pinned = replace(reference, revision=reference.revision or info.updated_at_utc)
        batch = self.catalog.read(
            pinned,
            start=settings.dataset.start,
            end=settings.dataset.end,
            count=_MAX_BARS + 1,
        )
        if batch.is_empty or batch.row_count > _MAX_BARS:
            raise DomainError(
                code="INVALID_DATASET", message="Dataset must contain 1 to 100000 bars"
            )
        bars = tuple(self._bar(row) for row in batch.frame.to_dicts())
        if any(b.time >= next_bar.time for b, next_bar in pairwise(bars)):
            raise DomainError(
                code="INVALID_DATASET",
                message="Market bars must be strictly chronological",
            )
        if (
            settings.split_time is not None
            and not bars[0].time < settings.split_time < bars[-1].time
        ):
            raise DomainError(
                code="INVALID_SAMPLE_BOUNDARY",
                message="Sample boundary must lie inside actual bars",
            )
        return pinned, bars

    def _read_strategies(
        self,
        project: ProjectDocument,
        settings: ExecutionSettings,
    ) -> list[str]:
        """Validate selected stored definitions and optimization dimensions."""
        strategies: list[str] = []
        for result_id in settings.strategy_result_ids:
            stored = self.results.get_result(result_id)
            if stored.databank_id not in project.databanks.values():
                raise DomainError(
                    code="STRATEGY_NOT_OWNED",
                    message="Selected strategy is outside project databanks",
                )
            try:
                strategy = _STRATEGY.validate_python(stored.strategy_payload)
            except (ValidationError, ValueError, TypeError) as error:
                raise DomainError(
                    code="INVALID_STRATEGY",
                    message="Stored strategy definition is invalid",
                ) from error
            if not strategy.rules or strategy.strategy_id != stored.strategy_id:
                raise DomainError(
                    code="INVALID_STRATEGY",
                    message="Stored strategy definition is missing or mismatched",
                )
            if settings.mode == "GRID":
                names = {p.name for p in strategy.params}
                if any(r.name not in names for r in settings.parameter_ranges):
                    raise DomainError(
                        code="INVALID_PARAMETER",
                        message="Optimization parameter is absent from strategy",
                    )
            strategies.append(_STRATEGY.dump_json(strategy).decode())
        return strategies

    @staticmethod
    def _bar(row: dict[str, Any]) -> MarketBar:
        timestamp = row.get("DateTime")
        if not isinstance(timestamp, datetime):
            raise DomainError(
                code="INVALID_DATASET",
                message="Catalog bar timestamps must be datetimes",
            )
        try:
            values = [float(row[key]) for key in ("Open", "High", "Low", "Close")]
            if not all(math.isfinite(value) and value > 0 for value in values):
                raise DomainError(
                    code="INVALID_DATASET",
                    message="Non-finite or nonpositive market price",
                )
            opening, high, low, close = values
            if low > min(opening, close) or high < max(opening, close) or high < low:
                raise DomainError(
                    code="INVALID_DATASET", message="Invalid OHLC envelope"
                )
            return MarketBar(
                int(
                    (
                        timestamp.astimezone(UTC)
                        if timestamp.tzinfo
                        else timestamp.replace(tzinfo=UTC)
                    ).timestamp()
                ),
                opening,
                high,
                low,
                close,
                int(row.get("Volume", 0)),
                int(row.get("Spread", 0)),
            )
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            raise DomainError(
                code="INVALID_DATASET", message="Catalog contains invalid OHLC bars"
            ) from error

    @staticmethod
    def _raw_candidates(
        snapshot: ExecutionSnapshot, config: ExecutionSettings
    ) -> tuple[StrategyDocument, ...]:
        if config.mode == "RANDOM":
            generator = GenerationEngine(
                GenerationSpec(
                    symbol=config.dataset.symbol,
                    timeframe=Timeframe(config.dataset.timeframe),
                    allowed_blocks=config.allowed_blocks,
                    max_rule_depth=config.max_rule_depth,
                    target_databank=snapshot.databank_id,
                    seed=config.seed,
                )
            )
            return tuple(
                generator.generate_random_strategy(f"{snapshot.task_id}-{i}")
                for i in range(config.candidates)
            )
        strategies = tuple(
            _STRATEGY.validate_json(raw) for raw in snapshot.strategies_json
        )
        if config.mode == "RETEST":
            return strategies
        indexes = OptimizationEngine().build_indexes(
            [
                ParameterRange(r.name, r.start, r.end, r.step)
                for r in config.parameter_ranges
            ]
        )
        original = strategies[0]
        return tuple(
            replace(
                original,
                params=tuple(
                    replace(p, value=indexes.get_params(i).get(p.name, p.value))
                    for p in original.params
                ),
            )
            for i in range(indexes.total_permutations)
        )

    @staticmethod
    def _candidates(
        snapshot: ExecutionSnapshot, config: ExecutionSettings
    ) -> tuple[StrategyDocument, ...]:
        candidates = ProjectExecutor._raw_candidates(snapshot, config)
        sizing = config.money_management
        if sizing is None:
            return candidates
        volume = FixedSize(size=sizing.size, decimals=sizing.decimals).compute_size(
            config.model.initial_capital, 0
        )
        if volume <= 0:
            raise DomainError(
                code="INVALID_POSITION_SIZE",
                message="Rounded position size must be positive",
            )
        return tuple(
            replace(
                strategy,
                rules=tuple(
                    replace(
                        rule,
                        actions=tuple(
                            replace(action, volume=volume)
                            if action.kind == ActionKind.ENTER
                            else action
                            for action in rule.actions
                        ),
                    )
                    for rule in strategy.rules
                ),
            )
            for strategy in candidates
        )

    def run(self, context: JobContext, snapshot: ExecutionSnapshot) -> dict[str, Any]:
        """Backtest candidates and explicitly reject non-finite results."""
        config = ExecutionSettings.model_validate_json(snapshot.config_json)
        candidates = self._candidates(snapshot, config)
        stored_ids: list[str] = []
        rejected = 0
        best_score: float | None = None
        best_parameters: dict[str, JSONValue] = {}
        for index, strategy in enumerate(candidates):
            context.wait_if_paused()
            context.check_memory_guard()
            context.raise_if_cancelled()
            result = BacktestRunner(StrategyRuntime()).run(
                RunSpec(
                    strategy,
                    config.dataset.symbol,
                    Timeframe(config.dataset.timeframe),
                    snapshot.bars,
                    config.model,
                )
            )
            split = (
                SampleSplit("DATE", datetime.fromtimestamp(config.split_time, UTC))
                if config.split_time is not None
                else SampleSplit()
            )
            statistics = StatisticsService().compute(
                result.trades, config.model.initial_capital, split
            )
            metrics = dict(result.metrics)
            for suffix, values in (
                ("is", statistics.in_sample),
                ("oos", statistics.out_of_sample),
            ):
                metrics.update(
                    {f"{key}_{suffix}": value for key, value in values.items()}
                )
            # ALL drawdown/equity stay with the simulation owner; trade statistics
            # supply the matching closed-trade metrics and actual sample partitions.
            metrics.update(
                {
                    key: statistics.all_trades[key]
                    for key in (
                        "net_profit",
                        "profit_factor",
                        "trades_count",
                        "win_rate",
                    )
                }
            )
            if not all(math.isfinite(value) for value in metrics.values()):
                rejected += 1
                logger.warning(
                    "FR-home-execution-finite: rejected non-finite candidate %d", index
                )
            else:
                context.wait_if_paused()
                context.raise_if_cancelled()
                parameters = cast(
                    "dict[str, JSONValue]", {p.name: p.value for p in strategy.params}
                )
                provenance: dict[str, JSONValue] = {
                    "project_id": snapshot.project_id,
                    "run_id": context.job_id,
                    "task_id": snapshot.task_id,
                    "project_revision": snapshot.project_revision,
                    "execution": json.loads(snapshot.config_json),
                    "parameters": parameters,
                    "sample_start": snapshot.bars[0].time,
                    "sample_end": snapshot.bars[-1].time,
                }
                stored = from_backtest_result(
                    replace(result, metrics=metrics),
                    result_id=f"{context.job_id}-{index}",
                    databank_id=snapshot.databank_id,
                    strategy_name=strategy.strategy_id,
                    parameters=provenance,
                    strategy_payload=cast(
                        "dict[str, JSONValue]",
                        _STRATEGY.dump_python(strategy, mode="json"),
                    ),
                )
                self.results.save_result(snapshot.databank_id, stored)
                if (
                    self.results.get_result(stored.result_id).to_dict()
                    != stored.to_dict()
                ):
                    raise DomainError(
                        code="RESULT_COMMIT_FAILED",
                        message="Stored result verification failed",
                    )
                stored_ids.append(stored.result_id)
                score = metrics["net_profit"]
                if best_score is None or score > best_score:
                    best_score, best_parameters = score, parameters
            context.report_progress(
                (index + 1) / len(candidates) * 100,
                (
                    f"Evaluated {index + 1}/{len(candidates)}; "
                    f"stored {len(stored_ids)}; rejected {rejected}"
                ),
            )
            logger.info(
                "FR-home-execution-evaluate: completed evaluation %d", index + 1
            )
        return {
            "project_id": snapshot.project_id,
            "task_id": snapshot.task_id,
            "databank_id": snapshot.databank_id,
            "candidates_evaluated": len(candidates),
            "candidates_accepted": len(stored_ids),
            "candidates_rejected": rejected,
            "result_ids": stored_ids,
            "best_fitness": best_score,
            "best_parameters": best_parameters,
        }
