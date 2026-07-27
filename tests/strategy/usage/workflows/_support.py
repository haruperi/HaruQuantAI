"""Shared, non-workflow infrastructure for Strategy workflow examples."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    StrategyDecision,
    StrategyExecutionContext,
    StrategyTimingPolicy,
)
from tests.indicators.usage.workflows._support import live_bars
from tests.strategy.unit.test_catalog import storage_context
from tests.strategy.unit.test_models import HASH, make_context, make_decision


class CurrentNeutralEvaluator:
    """Hash-bound evaluator returning one currently valid neutral decision."""

    strategy_id = "mean-reversion"
    strategy_version = "1.0.0"
    module_path = "approved.strategies.mean_reversion"
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH

    def evaluate_vectorized(
        self,
        market: object,
        indicators: object,
        config: object,
        context: StrategyExecutionContext,
        account_snapshot: object,
    ) -> tuple[StrategyDecision, ...]:
        """Return one neutral decision bound to the injected decision clock."""
        del market, indicators, config, account_snapshot
        return (
            make_decision(action="NEUTRAL").model_copy(
                update={
                    "valid_from": context.decision_timestamp - timedelta(seconds=1),
                    "expires_at": context.decision_timestamp + timedelta(seconds=1),
                }
            ),
        )


def current_context(
    timing: StrategyTimingPolicy = StrategyTimingPolicy.EVENT_DRIVEN,
) -> StrategyExecutionContext:
    """Build a fixed execution clock after the genuine market read."""
    return make_context(timing=timing).model_copy(
        update={"decision_timestamp": datetime.now(UTC) + timedelta(seconds=1)}
    )


@contextmanager
def temporary_storage() -> Iterator[Path]:
    """Activate bounded temporary Strategy registry persistence."""
    with TemporaryDirectory(prefix="strategy-workflow-") as raw:
        path = Path(raw)
        with storage_context(path):
            yield path


__all__ = [
    "CurrentNeutralEvaluator",
    "current_context",
    "live_bars",
    "temporary_storage",
]
